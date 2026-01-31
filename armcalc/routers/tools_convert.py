"""Conversion tools: price, convert, unit, rates."""

from decimal import Decimal
from typing import Optional, Tuple

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.services.price_service import get_price_service
from armcalc.services.fx_service import get_fx_service, ConversionResult
from armcalc.services.unit_service import get_unit_service
from armcalc.services.exswaping_xml_service import (
    get_xml_service,
    RUB_METHOD_ALIASES,
)
from armcalc.services.history_store import get_history_store
from armcalc.config import get_settings
from armcalc.utils.logging import get_logger

logger = get_logger("tools_convert")
router = Router(name="tools_convert")


def parse_float(value: str) -> float | None:
    """Parse a float from string, handling commas."""
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def parse_decimal(value: str) -> Decimal | None:
    """Parse a Decimal from string, handling commas."""
    try:
        return Decimal(value.replace(",", "").strip())
    except Exception:
        return None


def detect_rub_method(tokens: list[str]) -> Tuple[str, Optional[str]]:
    """
    Detect RUB payment method from tokens.

    Patterns supported:
    - ["rub", "sberbank"] -> ("RUB", "sberbank")
    - ["sberbank", "rub"] -> ("RUB", "sberbank")
    - ["sberbank_rub"] -> ("RUB", "sberbank")
    - ["sberrub"] -> ("RUB", "sberbank")
    - ["rub"] -> ("RUB", None)

    Returns (currency, method)
    """
    if not tokens:
        return ("", None)

    # Join tokens to handle multi-word
    combined = "_".join(tokens).lower()

    # Check for method_rub or rub_method patterns
    for alias, method in RUB_METHOD_ALIASES.items():
        if f"{alias}_rub" in combined or f"rub_{alias}" in combined:
            return ("RUB", method)
        if f"{alias}rub" in combined:
            return ("RUB", method)

    # Check individual tokens
    method_found = None
    has_rub = False

    for token in tokens:
        token_lower = token.lower()
        if token_lower == "rub":
            has_rub = True
        elif token_lower in RUB_METHOD_ALIASES:
            method_found = RUB_METHOD_ALIASES[token_lower]
            has_rub = True  # Implies RUB

    if has_rub:
        return ("RUB", method_found)

    # Return first token as currency if not RUB
    return (tokens[0].upper(), None)


def parse_convert_args(parts: list[str]) -> Tuple[Optional[Decimal], str, str, Optional[str]]:
    """
    Parse /convert command arguments.

    Supports patterns:
    - /convert 100 usd amd
    - /convert 100 usdt amd
    - /convert 100 usdt sberbank rub
    - /convert 100 usdt rub sberbank
    - /convert 100 usdt sberbank_rub

    Returns (amount, from_curr, to_curr, method)
    """
    if len(parts) < 4:
        return (None, "", "", None)

    amount = parse_decimal(parts[1])
    if amount is None:
        return (None, "", "", None)

    from_curr = parts[2].upper()

    # Remaining parts are the target
    to_parts = parts[3:]

    # Detect RUB method in target
    to_curr, method = detect_rub_method(to_parts)

    # If no method detected and single token, just use it as currency
    if not method and len(to_parts) == 1:
        to_curr = to_parts[0].upper()

    return (amount, from_curr, to_curr, method)


@router.message(Command("price", "p"))
async def cmd_price(message: Message) -> None:
    """
    Get cryptocurrency price.

    Usage: /price <symbol>
    Example: /price btc
    """
    if not message.text:
        return

    parts = message.text.split()

    if len(parts) < 2:
        price_service = get_price_service()
        symbols = ", ".join(price_service.get_supported_symbols()[:15])
        await message.answer(
            f"Usage: `/price <symbol>`\n"
            f"Example: `/price btc`\n\n"
            f"Supported: {symbols}...",
            parse_mode="Markdown",
        )
        return

    symbol = parts[1].lower().strip()
    price_service = get_price_service()

    # Send typing indicator for potentially slow API call
    await message.bot.send_chat_action(message.chat.id, "typing")

    price = await price_service.get_price(symbol)

    if price is None:
        await message.answer(
            f"Could not get price for '{symbol}'.\n"
            f"Try: btc, eth, sol, bnb, xrp, ada, doge, ltc"
        )
        return

    # Format change indicator
    change_str = ""
    if price.change_24h is not None:
        direction = "📈" if price.change_24h >= 0 else "📉"
        change_str = f"\n24h Change: {direction} {price.change_24h:+.2f}%"

    amd_str = ""
    if price.price_amd:
        amd_str = f"\nAMD: {price.formatted_amd}"

    result_text = (
        f"💰 **{price.name}** ({price.symbol.upper()})\n\n"
        f"USD: {price.formatted_usd}{amd_str}{change_str}"
    )

    # Save to history
    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()
    history.add_entry(user_id, f"price {symbol}", price.formatted_usd, "price")

    await message.answer(result_text, parse_mode="Markdown")


@router.message(Command("convert", "conv", "c"))
async def cmd_convert(message: Message) -> None:
    """
    Convert between currencies.

    Usage:
    - /convert 100 usd amd
    - /convert 100 usdt amd
    - /convert 100 amd usdt
    - /convert 100 usdt sberbank rub
    - /convert 100 usdt rub sberbank
    - /convert 100 usdt sberbank_rub

    Some pairs use exchanger XML rates (AMD<->USDT, USD<->USDT, RUB methods).
    """
    if not message.text:
        return

    parts = message.text.split()

    if len(parts) < 4:
        settings = get_settings()
        await message.answer(
            "Usage: `/convert <amount> <from> <to>`\n\n"
            "**Examples:**\n"
            "• `/convert 100 usd amd`\n"
            "• `/convert 100 usdt amd`\n"
            "• `/convert 100 amd usdt`\n"
            "• `/convert 100 usdt sberbank rub`\n"
            "• `/convert 100 usdt tinkoff rub`\n\n"
            f"**RUB methods:** sberbank, tinkoff, alfa, vtb\n"
            f"Default RUB method: {settings.default_rub_method}\n\n"
            "Use `/rates usdt` to see available targets.",
            parse_mode="Markdown",
        )
        return

    amount, from_curr, to_curr, method = parse_convert_args(parts)

    if amount is None:
        await message.answer("Invalid amount.", parse_mode="Markdown")
        return

    if amount <= 0:
        await message.answer("Amount must be positive.")
        return

    # Send typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()
    settings = get_settings()

    # Try XML service first for priority pairs
    xml_service = get_xml_service()

    if xml_service.is_xml_pair(from_curr, to_curr, method):
        # Try XML rates
        rate_quote = await xml_service.get_rate(from_curr, to_curr, method)

        if rate_quote:
            result_amount = rate_quote.convert(amount)
            used_method = rate_quote.method

            # Format output
            if used_method:
                to_display = f"RUB ({used_method.title()})"
            else:
                to_display = to_curr

            # Format amounts
            if to_curr in ("AMD", "RUB") or (to_curr == "RUB" and used_method):
                result_str = f"{result_amount:,.0f}"
            else:
                result_str = f"{result_amount:,.2f}"

            if from_curr in ("AMD", "RUB"):
                amount_str = f"{amount:,.0f}"
            else:
                amount_str = f"{amount:,.2f}"

            result_text = (
                f"💱 **Currency Conversion**\n\n"
                f"{amount_str} {from_curr} → {result_str} {to_display}\n\n"
                f"Rate: 1 {from_curr} = {rate_quote.rate:.4f} {to_display}\n"
                f"_Source: exchanger rates_"
            )

            history.add_entry(
                user_id,
                f"{amount} {from_curr} -> {to_display}",
                f"{result_str} {to_display}",
                "convert",
            )

            await message.answer(result_text, parse_mode="Markdown")
            return

    # Fallback to fx_service
    fx_service = get_fx_service()
    result = await fx_service.convert(float(amount), from_curr, to_curr)

    if result is None:
        # Try to give helpful error
        if to_curr == "RUB" and not method:
            await message.answer(
                f"Could not convert {from_curr} to {to_curr}.\n\n"
                f"For RUB, try specifying a method:\n"
                f"`/convert {amount} {from_curr} sberbank rub`",
                parse_mode="Markdown",
            )
        else:
            await message.answer(
                f"Could not convert {from_curr} to {to_curr}.\n"
                f"Check currency codes and try again.\n"
                f"Use `/rates {from_curr.lower()}` to see available targets."
            )
        return

    result_text = (
        f"💱 **Currency Conversion**\n\n"
        f"{result.formatted}\n\n"
        f"Rate: 1 {from_curr} = {result.rate:.4f} {to_curr}\n"
        f"_Source: public FX rates_"
    )

    history.add_entry(
        user_id,
        f"{amount} {from_curr} -> {to_curr}",
        result.formatted,
        "convert",
    )

    await message.answer(result_text, parse_mode="Markdown")


@router.message(Command("rates", "pairs"))
async def cmd_rates(message: Message) -> None:
    """
    Show available exchange rates from XML.

    Usage:
    - /rates - show all directions
    - /rates usdt - show targets for USDT
    - /rates rub - show RUB methods
    """
    if not message.text:
        return

    parts = message.text.split()
    xml_service = get_xml_service()

    # Send typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    if len(parts) < 2:
        # Show summary
        directions = await xml_service.list_directions()

        if not directions:
            await message.answer(
                "No exchange rates available.\n"
                "The exchanger XML may be temporarily unavailable."
            )
            return

        # Group by from currency
        from_currencies = {}
        for d in directions:
            if d.from_code not in from_currencies:
                from_currencies[d.from_code] = []
            target = d.display_to
            if target not in from_currencies[d.from_code]:
                from_currencies[d.from_code].append(target)

        lines = ["📊 **Available Exchange Rates**\n"]
        for from_c, targets in sorted(from_currencies.items()):
            targets_str = ", ".join(sorted(targets)[:5])
            if len(targets) > 5:
                targets_str += f"... (+{len(targets) - 5})"
            lines.append(f"**{from_c}** → {targets_str}")

        lines.append("\n_Use `/rates <currency>` for details_")
        lines.append("_Some pairs use exchanger XML rates_")

        await message.answer("\n".join(lines), parse_mode="Markdown")
        return

    # Show rates for specific currency
    filter_code = parts[1].upper()

    # Check if it's a method query
    if filter_code.lower() in RUB_METHOD_ALIASES:
        method = RUB_METHOD_ALIASES[filter_code.lower()]
        directions = await xml_service.list_directions()
        matching = [d for d in directions if d.method == method]

        if not matching:
            await message.answer(f"No rates found for method '{method}'.")
            return

        lines = [f"📊 **Rates for {method.title()}**\n"]
        for d in matching:
            lines.append(f"{d.from_code} → {d.display_to}: **{d.rate:.4f}**")

        await message.answer("\n".join(lines), parse_mode="Markdown")
        return

    # Query as source currency
    directions = await xml_service.list_directions(filter_from=filter_code)

    if not directions:
        # Try as target
        directions = await xml_service.list_directions(filter_to=filter_code)
        if directions:
            lines = [f"📊 **Rates to {filter_code}**\n"]
            for d in directions:
                method_str = f" ({d.method})" if d.method else ""
                lines.append(f"{d.from_code} → {d.display_to}: **{d.rate:.4f}**{method_str}")
            await message.answer("\n".join(lines), parse_mode="Markdown")
            return

        await message.answer(
            f"No rates found for '{filter_code}'.\n"
            f"Use `/rates` to see available currencies."
        )
        return

    lines = [f"📊 **Rates from {filter_code}**\n"]
    for d in directions:
        method_str = f" ({d.method})" if d.method else ""
        min_max = ""
        if d.min_amount and d.max_amount:
            min_max = f" [{d.min_amount}-{d.max_amount}]"
        lines.append(f"→ {d.display_to}: **{d.rate:.4f}**{method_str}{min_max}")

    lines.append("\n_Use `/convert <amount> <from> <to>` to convert_")

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("unit", "u"))
async def cmd_unit(message: Message) -> None:
    """
    Convert between units.

    Usage: /unit <amount> <from_unit> <to_unit>
    Example: /unit 10 km miles
    """
    if not message.text:
        return

    parts = message.text.split()

    if len(parts) < 4:
        unit_service = get_unit_service()
        categories = unit_service.get_supported_units()
        help_lines = ["Usage: `/unit <amount> <from> <to>`", "Example: `/unit 10 km miles`", ""]
        for cat, units in list(categories.items())[:4]:
            help_lines.append(f"**{cat.title()}**: {', '.join(units[:6])}")
        await message.answer("\n".join(help_lines), parse_mode="Markdown")
        return

    amount = parse_float(parts[1])
    from_unit = parts[2].lower()
    to_unit = parts[3].lower()

    if amount is None:
        await message.answer("Invalid amount.", parse_mode="Markdown")
        return

    unit_service = get_unit_service()
    result = unit_service.convert(amount, from_unit, to_unit)

    if result is None:
        await message.answer(
            f"Cannot convert '{from_unit}' to '{to_unit}'.\n"
            f"Check unit names. Use `/unit` to see supported units."
        )
        return

    result_text = (
        f"📐 **Unit Conversion** ({result.category})\n\n"
        f"**{result.formatted}**"
    )

    # Save to history
    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()
    history.add_entry(
        user_id,
        f"{amount} {from_unit} -> {to_unit}",
        result.formatted,
        "unit",
    )

    await message.answer(result_text, parse_mode="Markdown")
