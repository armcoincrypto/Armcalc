"""Conversion tools: price, convert, rates."""

from decimal import Decimal
from typing import Dict, Optional, Tuple

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from armcalc.services.price_service import get_price_service
from armcalc.services.fx_service import get_fx_service, ConversionResult
from armcalc.services.exswaping_xml_service import (
    get_xml_service,
    RUB_METHOD_ALIASES,
)
from armcalc.services.history_store import get_history_store
from armcalc.services.convert_state import (
    get_user_state,
    save_user_state,
    clear_user_state,
    has_active_state,
    set_amount,
    set_from_code,
    set_to_code,
    swap_currencies,
    set_usdt_network,
    set_amd_unit,
    set_rub_method,
    set_result,
    get_xml_codes,
    AvailabilityResult,
)
from armcalc.keyboards.convert_panel import (
    ConvertPanelCallback,
    get_convert_panel_keyboard,
    render_panel_text,
)
from armcalc.config import get_settings
from armcalc.utils.logging import get_logger

logger = get_logger("tools_convert")
router = Router(name="tools_convert")


async def _get_available_pairs(xml_service) -> set:
    """
    Get set of available (from_xml, to_xml) pairs from XML service.

    Returns set of tuples for fast lookup using RAW XML codes.
    """
    directions = await xml_service.list_directions()
    pairs = set()

    for d in directions:
        from_code = d.from_code.upper()
        to_code = d.to_code.upper()
        pairs.add((from_code, to_code))

    return pairs


async def check_pair_available_async(
    xml_service,
    from_code: str,
    to_code: str,
    method: Optional[str] = None,
) -> bool:
    """
    Check if a specific pair is available using xml_service.get_rate().

    This is the authoritative check - if get_rate() returns a value,
    the pair is available. This matches exactly what the convert action uses.
    """
    rate = await xml_service.get_rate(from_code, to_code, method)
    return rate is not None


async def check_availability_async(
    state,
    xml_service,
) -> "AvailabilityResult":
    """
    Async version of check_availability that uses xml_service.get_rate() directly.

    This is more accurate than the set-based check because it uses the same
    lookup logic that the actual conversion uses.
    """
    from armcalc.services.convert_state import (
        AvailabilityResult,
        involves_rub,
        USDT_NETWORKS,
        RUB_METHODS,
        AMD_UNITS,
    )

    # Get the codes that will be used for conversion
    from_code, to_code, method = get_xml_codes(state)

    # Check if pair is available using actual xml_service lookup
    rate = await xml_service.get_rate(state.from_code, state.to_code, method)

    if rate is not None:
        return AvailabilityResult(
            available=True,
            from_xml=rate.from_code,
            to_xml=rate.to_code,
            method=rate.method,
        )

    # Not available - find suggestions by trying alternatives
    suggestions = []
    reason = f"{state.from_code.upper()} → {state.to_code.upper()} not available"

    # Try alternative AMD units
    if state.to_code == "amd":
        for unit in AMD_UNITS:
            if unit == state.amd_unit:
                continue
            # Temporarily check with different unit
            test_to = "CASHAMD" if unit == "cash" else "CARDAMD"
            if await xml_service.get_rate(state.from_code, test_to, method):
                suggestions.append(("amd_unit", unit, f"AMD {unit.title()}"))
                reason = f"AMD {state.amd_unit.title()} not available"
                break

    if state.from_code == "amd":
        for unit in AMD_UNITS:
            if unit == state.amd_unit:
                continue
            test_from = "CASHAMD" if unit == "cash" else "CARDAMD"
            if await xml_service.get_rate(test_from, state.to_code, method):
                suggestions.append(("amd_unit", unit, f"AMD {unit.title()}"))
                reason = f"AMD {state.amd_unit.title()} not available"
                break

    # Try alternative USDT networks
    if state.from_code == "usdt":
        for net in USDT_NETWORKS:
            if net == state.usdt_network:
                continue
            test_from = f"USDT{net.upper()}"
            if await xml_service.get_rate(test_from, state.to_code, method):
                suggestions.append(("network", net, f"USDT {net.upper()}"))
                reason = f"USDT {state.usdt_network.upper()} not available"
                break

    if state.to_code == "usdt":
        for net in USDT_NETWORKS:
            if net == state.usdt_network:
                continue
            test_to = f"USDT{net.upper()}"
            if await xml_service.get_rate(state.from_code, test_to, method):
                suggestions.append(("network", net, f"USDT {net.upper()}"))
                reason = f"USDT {state.usdt_network.upper()} not available"
                break

    # Try alternative RUB methods
    if state.to_code == "rub":
        for meth in RUB_METHODS:
            if meth == state.rub_method:
                continue
            if await xml_service.get_rate(state.from_code, "RUB", meth):
                suggestions.append(("rub_method", meth, f"RUB {meth.title()}"))
                reason = f"RUB {state.rub_method.title()} not available"
                break

    if state.from_code == "rub":
        for meth in RUB_METHODS:
            if meth == state.rub_method:
                continue
            if await xml_service.get_rate("RUB", state.to_code, meth):
                suggestions.append(("rub_method", meth, f"RUB {meth.title()}"))
                reason = f"RUB {state.rub_method.title()} not available"
                break

    return AvailabilityResult(
        available=False,
        from_xml=from_code,
        to_xml=to_code,
        method=method,
        reason=reason,
        suggestions=suggestions[:3],
    )


async def auto_fix_state_async(
    state,
    xml_service,
):
    """
    Async version of auto_fix_state that uses xml_service directly.

    Returns (fixed_state, availability_result).
    """
    from armcalc.services.convert_state import (
        set_amd_unit,
        set_usdt_network,
        set_rub_method,
        AUTO_FIX_UNAVAILABLE,
    )

    result = await check_availability_async(state, xml_service)

    if result.available or not AUTO_FIX_UNAVAILABLE:
        return state, result

    # Apply first suggestion
    if result.suggestions:
        action, value, display = result.suggestions[0]

        if action == "amd_unit":
            old_val = state.amd_unit.title()
            state = set_amd_unit(state, value)
            result.adjusted = True
            result.adjustment_msg = f"AMD {old_val} → AMD {value.title()} (not available)"

        elif action == "network":
            old_val = state.usdt_network.upper()
            state = set_usdt_network(state, value)
            result.adjusted = True
            result.adjustment_msg = f"USDT {old_val} → USDT {value.upper()} (not available)"

        elif action == "rub_method":
            old_val = state.rub_method.title()
            state = set_rub_method(state, value)
            result.adjusted = True
            result.adjustment_msg = f"RUB {old_val} → RUB {value.title()} (not available)"

        # Re-check after fix
        new_result = await check_availability_async(state, xml_service)
        new_result.adjusted = result.adjusted
        new_result.adjustment_msg = result.adjustment_msg
        return state, new_result

    return state, result


async def get_allowed_options_async(
    state,
    xml_service,
) -> Dict[str, set]:
    """
    Async version of get_allowed_options that uses xml_service directly.

    Returns dict with keys: networks, amd_units, rub_methods
    """
    from armcalc.services.convert_state import (
        USDT_NETWORKS,
        AMD_UNITS,
        RUB_METHODS,
    )

    allowed = {
        "networks": set(),
        "amd_units": set(),
        "rub_methods": set(),
    }
    method = state.rub_method if state.from_code == "rub" or state.to_code == "rub" else None

    # Check USDT networks
    if state.from_code == "usdt" or state.to_code == "usdt":
        for net in USDT_NETWORKS:
            test_from = state.from_code
            test_to = state.to_code
            if state.from_code == "usdt":
                test_from = f"USDT{net.upper()}"
            if state.to_code == "usdt":
                test_to = f"USDT{net.upper()}"
            if await xml_service.get_rate(test_from, test_to, method):
                allowed["networks"].add(net)

    # Check AMD units
    if state.from_code == "amd" or state.to_code == "amd":
        for unit in AMD_UNITS:
            test_from = state.from_code
            test_to = state.to_code
            if state.from_code == "amd":
                test_from = "CASHAMD" if unit == "cash" else "CARDAMD"
            if state.to_code == "amd":
                test_to = "CASHAMD" if unit == "cash" else "CARDAMD"
            if await xml_service.get_rate(test_from, test_to, method):
                allowed["amd_units"].add(unit)

    # Check RUB methods
    if state.from_code == "rub" or state.to_code == "rub":
        for meth in RUB_METHODS:
            if await xml_service.get_rate(state.from_code, state.to_code, meth):
                allowed["rub_methods"].add(meth)

    return allowed


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


def get_default_disclosure(user_code: str, xml_code: str, settings) -> Optional[str]:
    """
    Get disclosure message if a default was used.

    Returns message like "Using USDT TRC20 (default)" if user typed "usdt"
    but we resolved to "USDTTRC20".
    """
    user_upper = user_code.upper().strip()

    # Check if user typed generic code that was normalized to specific unit
    if user_upper == "USDT" and xml_code.upper() != "USDT":
        network = xml_code.upper().replace("USDT", "")
        return f"USDT {network} network"

    if user_upper == "AMD" and xml_code.upper() not in ("AMD",):
        variant = xml_code.upper().replace("AMD", "")
        return f"AMD {variant.title()}"

    if user_upper == "USD" and xml_code.upper() not in ("USD",):
        variant = xml_code.upper().replace("USD", "")
        return f"USD {variant.title()}"

    return None


def parse_convert_args(parts: list[str]) -> Tuple[Optional[Decimal], str, str, Optional[str]]:
    """
    Parse /convert command arguments.

    Supports natural patterns:
    - /convert 100 usd amd
    - /convert 100 usdt amd
    - /convert 100 usdt -> amd
    - /convert 100 usdt to amd
    - /convert 100 usdt/amd
    - /convert 100 usdt sberbank rub
    - /convert 100 usdt rub sberbank
    - /convert 100 usdt sberbank_rub

    Returns (amount, from_curr, to_curr, method)
    """
    if len(parts) < 2:
        return (None, "", "", None)

    # Clean and normalize tokens
    # Remove arrows and separators, handle "usdt/amd" format
    cleaned = []
    for p in parts[1:]:  # Skip command
        # Handle "usdt/amd" or "usdt->amd" in single token
        p = p.replace("->", " ").replace("→", " ").replace("/", " ")
        for token in p.split():
            token = token.strip().lower()
            # Skip filler words
            if token in ("to", "->", "→", "=", "in"):
                continue
            if token:
                cleaned.append(token)

    if len(cleaned) < 3:
        return (None, "", "", None)

    # First token should be amount
    amount = parse_decimal(cleaned[0])
    if amount is None:
        return (None, "", "", None)

    from_curr = cleaned[1].upper()

    # Remaining parts are the target
    to_parts = cleaned[2:]

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
            f"Usage: <code>/price btc</code>\n\n"
            f"Supported: {symbols}...",
            parse_mode="HTML",
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
        f"💰 <b>{price.name}</b> ({price.symbol.upper()})\n\n"
        f"USD: {price.formatted_usd}{amd_str}{change_str}"
    )

    # Save to history
    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()
    history.add_entry(user_id, f"price {symbol}", price.formatted_usd, "price")

    await message.answer(result_text, parse_mode="HTML")


@router.message(Command("convert", "conv", "c"))
async def cmd_convert(message: Message) -> None:
    """
    Convert between currencies.

    - With args: text-based conversion (e.g., /convert 100 usdt amd)
    - Without args: interactive panel UI
    """
    if not message.text:
        return

    user_id = message.from_user.id if message.from_user else 0
    parts = message.text.split()
    logger.info(f"/convert from user {user_id}: {message.text}")

    # If no arguments, show interactive panel
    if len(parts) == 1:
        state = get_user_state(user_id)
        save_user_state(user_id, state)

        await message.answer(
            render_panel_text(state, None),
            reply_markup=get_convert_panel_keyboard(state, None),
            parse_mode="HTML",
        )
        return

    # If insufficient args for text conversion, show help
    if len(parts) < 4:
        await message.answer(
            "💱 <b>Convert Currency</b>\n\n"
            "<b>Examples:</b>\n"
            "<code>/convert 100 usdt amd</code>\n"
            "<code>/convert 50000 amd usdt</code>\n"
            "<code>/convert 100 usdt sberbank rub</code>\n\n"
            "<b>Defaults:</b> USDT=TRC20, AMD=Cash, RUB=Sberbank\n"
            "<i>Or use /convert for interactive panel</i>",
            parse_mode="HTML",
        )
        return

    amount, from_curr, to_curr, method = parse_convert_args(parts)

    if amount is None:
        await message.answer("Invalid amount.", parse_mode="HTML")
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

            # Get display names
            from_display = rate_quote.display_from
            to_display = rate_quote.display_to

            # Format amounts (no decimals for AMD/RUB)
            to_code_upper = rate_quote.to_code.upper()
            if "AMD" in to_code_upper or "RUB" in to_code_upper:
                result_str = f"{result_amount:,.0f}"
            else:
                result_str = f"{result_amount:,.2f}"

            from_code_upper = rate_quote.from_code.upper()
            if "AMD" in from_code_upper or "RUB" in from_code_upper:
                amount_str = f"{amount:,.0f}"
            else:
                amount_str = f"{amount:,.2f}"

            # Check if defaults were used and build disclosure
            disclosures = []
            from_disc = get_default_disclosure(from_curr, rate_quote.from_code, settings)
            to_disc = get_default_disclosure(to_curr, rate_quote.to_code, settings)
            if from_disc:
                disclosures.append(from_disc)
            if to_disc:
                disclosures.append(to_disc)
            if to_curr.upper() == "RUB" and not method and rate_quote.method:
                disclosures.append(f"RUB {rate_quote.method.title()}")

            # Build result text
            result_text = (
                f"💱 <b>Conversion</b>\n\n"
                f"{amount_str} {from_display} → {result_str} {to_display}\n"
                f"Rate: 1 {from_display} = {rate_quote.rate:.4f} {to_display}"
            )

            # Add disclosure if defaults were used
            if disclosures:
                result_text += f"\n\n<i>Using: {', '.join(disclosures)} (default)</i>"
                result_text += "\n<i>See /pairs for other options</i>"

            history.add_entry(
                user_id,
                f"{amount} {from_display} -> {to_display}",
                f"{result_str} {to_display}",
                "convert",
            )

            await message.answer(result_text, parse_mode="HTML")
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
                f"<code>/convert {amount} {from_curr} sberbank rub</code>",
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"Could not convert {from_curr} to {to_curr}.\n"
                f"Check currency codes and try again.",
                parse_mode="HTML",
            )
        return

    result_text = (
        f"💱 <b>Conversion</b>\n\n"
        f"{result.formatted}\n"
        f"Rate: 1 {from_curr} = {result.rate:.4f} {to_curr}"
    )

    history.add_entry(
        user_id,
        f"{amount} {from_curr} -> {to_curr}",
        result.formatted,
        "convert",
    )

    await message.answer(result_text, parse_mode="HTML")


@router.message(Command("pairs"))
async def cmd_pairs(message: Message) -> None:
    """
    Show available networks/methods for a currency.

    Usage:
    - /pairs usdt - show USDT networks
    - /pairs rub - show RUB payment methods
    - /pairs amd - show AMD options
    """
    if not message.text:
        return

    user_id = message.from_user.id if message.from_user else 0
    parts = message.text.split()
    logger.info(f"/pairs from user {user_id}, args: {parts[1:] if len(parts) > 1 else 'none'}")

    xml_service = get_xml_service()
    await message.bot.send_chat_action(message.chat.id, "typing")

    if len(parts) < 2:
        # Show overview
        lines = [
            "📊 <b>Available Pairs</b>\n",
            "<b>USDT networks:</b>",
            "• TRC20 (default), BEP20, ERC20",
            "• Specify: <code>/convert 100 usdttrc20 amd</code>\n",
            "<b>AMD options:</b>",
            "• Cash (default), Card",
            "• Specify: <code>/convert 100 usdt cardamd</code>\n",
            "<b>RUB methods:</b>",
            "• sberbank (default), tinkoff, alfa, vtb",
            "• Specify: <code>/convert 100 usdt sberbank rub</code>\n",
            "<b>Crypto:</b>",
            "• BTC, ETH, TON, SOL, XRP, LTC, DOGE\n",
            "Use <code>/pairs usdt</code> for detailed rates.",
        ]
        await message.answer("\n".join(lines), parse_mode="HTML")
        return

    currency = parts[1].upper().strip()

    # Show pairs for this currency
    if currency in ("USDT", "USDTTRC20", "USDTBEP20", "USDTERC20"):
        # USDT -> various targets
        lines = ["📊 <b>USDT Pairs</b>\n"]

        # Networks available
        lines.append("<b>Networks:</b>")
        lines.append("• TRC20 (default) - lowest fees")
        lines.append("• BEP20 - Binance Smart Chain")
        lines.append("• ERC20 - Ethereum (higher fees)\n")

        # Targets
        lines.append("<b>Convert to:</b>")
        rate = await xml_service.get_rate("USDT", "AMD")
        if rate:
            lines.append(f"• AMD (Cash): 1 USDT = {rate.rate:.2f} AMD")
        rate = await xml_service.get_rate("USDT", "CARDAMD")
        if rate:
            lines.append(f"• AMD (Card): 1 USDT = {rate.rate:.2f} AMD")

        for method in ["sberbank", "tinkoff", "alfabank"]:
            rate = await xml_service.get_rate("USDT", "RUB", method)
            if rate:
                lines.append(f"• RUB ({method.title()}): 1 USDT = {rate.rate:.2f} RUB")

        lines.append("\n<b>Examples:</b>")
        lines.append("<code>/convert 100 usdt amd</code>")
        lines.append("<code>/convert 100 usdt sberbank rub</code>")

        await message.answer("\n".join(lines), parse_mode="HTML")

    elif currency in ("AMD", "CASHAMD", "CARDAMD"):
        lines = ["📊 <b>AMD Pairs</b>\n"]
        lines.append("<b>Options:</b>")
        lines.append("• Cash (default)")
        lines.append("• Card\n")

        lines.append("<b>Convert to:</b>")
        rate = await xml_service.get_rate("AMD", "USDT")
        if rate:
            inverse = 1 / rate.rate if rate.rate else 0
            lines.append(f"• USDT: {inverse:.2f} AMD = 1 USDT")

        lines.append("\n<b>Examples:</b>")
        lines.append("<code>/convert 50000 amd usdt</code>")
        lines.append("<code>/convert 50000 cardamd usdt</code>")

        await message.answer("\n".join(lines), parse_mode="HTML")

    elif currency == "RUB":
        lines = ["📊 <b>RUB Payment Methods</b>\n"]
        settings = get_settings()
        lines.append(f"<b>Default:</b> {settings.default_rub_method}\n")

        lines.append("<b>Available:</b>")
        for method in ["sberbank", "tinkoff", "alfabank", "vtb"]:
            rate = await xml_service.get_rate("USDT", "RUB", method)
            if rate:
                lines.append(f"• {method.title()}: 1 USDT = {rate.rate:.2f} RUB")

        lines.append("\n<b>Examples:</b>")
        lines.append("<code>/convert 100 usdt sberbank rub</code>")
        lines.append("<code>/convert 100 usdt tinkoff rub</code>")

        await message.answer("\n".join(lines), parse_mode="HTML")

    else:
        # Try to show what's available for this crypto
        directions = await xml_service.list_directions(filter_from=currency)
        if directions:
            lines = [f"📊 <b>{currency} Pairs</b>\n"]
            usdt_dirs = [d for d in directions if "USDT" in d.to_code]
            if usdt_dirs:
                d = usdt_dirs[0]
                lines.append(f"• {currency} → USDT: {d.rate:.2f}")
            lines.append(f"\n<b>Example:</b>")
            lines.append(f"<code>/convert 1 {currency.lower()} usdt</code>")
            await message.answer("\n".join(lines), parse_mode="HTML")
        else:
            await message.answer(
                f"No pairs found for {currency}.\n\n"
                "Try: <code>/pairs usdt</code>, <code>/pairs amd</code>, <code>/pairs rub</code>",
                parse_mode="HTML",
            )


@router.message(Command("rates"))
async def cmd_rates(message: Message) -> None:
    """
    Show exchange rates - main pairs and crypto.
    """
    if not message.text:
        return

    user_id = message.from_user.id if message.from_user else 0
    logger.info(f"/rates from user {user_id}")

    xml_service = get_xml_service()

    # Send typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    lines = ["📊 <b>Exchange Rates</b>\n"]

    # USDT <-> AMD
    lines.append("<b>USDT ↔ AMD</b>")
    rate = await xml_service.get_rate("USDT", "AMD")
    if rate:
        lines.append(f"  Buy AMD: 1 USDT = {rate.rate:.2f} AMD")
    rate = await xml_service.get_rate("AMD", "USDT")
    if rate:
        lines.append(f"  Sell AMD: {1/rate.rate:.2f} AMD = 1 USDT")

    lines.append("")

    # USDT -> RUB methods
    lines.append("<b>USDT → RUB</b>")
    for method in ["sberbank", "tinkoff", "alfabank"]:
        rate = await xml_service.get_rate("USDT", "RUB", method)
        if rate:
            lines.append(f"  {method.title()}: 1 USDT = {rate.rate:.2f} RUB")

    lines.append("")

    # Crypto -> USDT
    lines.append("<b>Crypto → USDT</b>")
    cryptos = ["BTC", "ETH", "TON", "SOL", "XRP", "LTC", "DOGE"]
    for crypto in cryptos:
        # Try to find rate from crypto to USDT
        directions = await xml_service.list_directions(filter_from=crypto)
        usdt_dirs = [d for d in directions if "USDT" in d.to_code]
        if usdt_dirs:
            d = usdt_dirs[0]
            lines.append(f"  {crypto}: {d.rate:.2f} USDT")

    await message.answer("\n".join(lines), parse_mode="HTML")


# =============================================================================
# Convert Panel Callback Handlers
# =============================================================================

# Pair ID to XML lookup mapping: (from_code, to_code, method, display_name, city)
# Actual codes from exswaping.com XML
# City codes: ERVN = Yerevan, LOSAN = Los Angeles
PAIR_MAPPINGS = {
    # ═══ USDT → CASH ═══
    "usdt_to_usd_evn": ("USDTTRC20", "CASHUSD", None, "USD Cash", "ERVN"),
    "usdt_to_amd_evn": ("USDTTRC20", "CASHAMD", None, "AMD Cash", "ERVN"),
    "usdt_to_usd_la": ("USDTTRC20", "CASHUSD", None, "USD Cash", "LOSAN"),

    # ═══ USDT → CARD ═══
    "usdt_to_amd_card": ("USDTTRC20", "CARDAMD", None, "AMD Card", None),
    "usdt_to_rub_card": ("USDTTRC20", "CARDRUB", None, "RUB Card", None),
    "usdt_to_kzt_card": ("USDTTRC20", "CARDKZT", None, "KZT Card", None),
    "usdt_to_gel_card": ("USDTTRC20", "CARDGEL", None, "GEL Card", None),
    "usdt_to_aed_card": ("USDTTRC20", "CARDAED", None, "AED Card", None),

    # ═══ CASH → USDT ═══
    "amd_evn_to_usdt": ("CASHAMD", "USDTTRC20", None, "USDT", "ERVN"),
    "usd_evn_to_usdt": ("CASHUSD", "USDTTRC20", None, "USDT", "ERVN"),
    "usd_la_to_usdt": ("CASHUSD", "USDTTRC20", None, "USDT", "LOSAN"),

    # ═══ CARD/BANK → USDT ═══
    "rub_card_to_usdt": ("SBERRUB", "USDTTRC20", None, "USDT", None),
}


@router.callback_query(ConvertPanelCallback.filter())
async def handle_convert_panel_callback(
    callback: CallbackQuery,
    callback_data: ConvertPanelCallback,
) -> None:
    """Handle convert panel callbacks - clean new design."""
    user_id = callback.from_user.id if callback.from_user else 0
    action = callback_data.action
    value = callback_data.value

    logger.debug(f"Convert panel: user={user_id}, action={action}, value={value}")

    state = get_user_state(user_id)

    # Get XML service
    xml_service = get_xml_service()
    await xml_service.ensure_cache()

    # Handle noop (section headers)
    if action == "noop" or action == "show_amount":
        await callback.answer()
        return

    # Handle close
    if action == "close":
        clear_user_state(user_id)
        await callback.message.delete()
        await callback.answer("Closed")
        return

    # Handle quick amount
    if action == "quick_amount":
        state, error = set_amount(state, value)
        if error:
            await callback.answer(error, show_alert=True)
            return
        state.last_result = None  # Clear result when amount changes
        save_user_state(user_id, state)
        await callback.answer(f"{value} USDT")

        # Update panel
        try:
            await callback.message.edit_text(
                render_panel_text(state, None),
                reply_markup=get_convert_panel_keyboard(state, None),
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    # Handle amount edit prompt
    if action == "amount":
        await callback.answer("Type amount in chat", show_alert=False)
        try:
            await callback.message.edit_text(
                render_panel_text(state, None) + "\n\n✏️ <i>Type amount in chat...</i>",
                reply_markup=get_convert_panel_keyboard(state, None),
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

    # Handle pair conversion
    if action == "pair":
        pair_id = value
        if pair_id not in PAIR_MAPPINGS:
            await callback.answer("Unknown pair", show_alert=True)
            return

        from_code, to_code, method, display_name, city = PAIR_MAPPINGS[pair_id]

        # Determine if this is "Sell USDT" or "Buy USDT"
        # Check if from_code starts with USDT (covers USDTTRC20, USDTERC20, etc.)
        is_sell_usdt = from_code.upper().startswith("USDT")

        await callback.answer("Converting...")

        # Get rate and convert (pass city for location-specific rates)
        rate_quote = await xml_service.get_rate(from_code, to_code, method, city)

        if rate_quote:
            result_amount = rate_quote.convert(state.amount)

            # Format based on direction
            if is_sell_usdt:
                # Sell USDT: "100 USDT → 37,500 AMD Card"
                amount_str = f"{state.amount:,.0f} USDT"
                to_upper = to_code.upper()
                if "AMD" in to_upper or "RUB" in to_upper or "KZT" in to_upper or "GEL" in to_upper or "AED" in to_upper:
                    result_str = f"{amount_str} → {result_amount:,.0f} {display_name}"
                else:
                    result_str = f"{amount_str} → {result_amount:,.2f} {display_name}"
                rate_str = f"1 USDT = {rate_quote.rate:.2f} {display_name}"
            else:
                # Buy USDT: "100,000 AMD → 256.41 USDT"
                # Clean up from_code for display
                from_display = from_code.replace("CASH", "").replace("SBER", "Sber ")
                amount_str = f"{state.amount:,.0f} {from_display}"
                result_str = f"{amount_str} → {result_amount:,.2f} USDT"
                rate_str = f"{rate_quote.rate:.0f} {from_display} = 1 USDT"

            state = set_result(state, result_str, rate_str)
            save_user_state(user_id, state)

            # Save to history
            history = get_history_store()
            history.add_entry(
                user_id,
                f"{amount_str} -> {display_name}",
                result_str,
                "convert",
            )
        else:
            state = set_result(state, f"{display_name} - not available", "")
            save_user_state(user_id, state)

        # Update panel with result
        try:
            await callback.message.edit_text(
                render_panel_text(state, None),
                reply_markup=get_convert_panel_keyboard(state, None),
                parse_mode="HTML",
            )
        except Exception:
            pass
        return

# =============================================================================
# Convert Panel Amount Input Handler
# =============================================================================


def _looks_like_number(text: str) -> bool:
    """Check if text looks like a number (for amount input)."""
    if not text:
        return False
    # Clean and check
    cleaned = text.replace(",", "").replace(" ", "").strip()
    if not cleaned:
        return False
    # Must start with digit or decimal
    if not (cleaned[0].isdigit() or cleaned[0] == "."):
        return False
    # Try to parse
    try:
        val = float(cleaned)
        return val > 0 and val < 1_000_000_000
    except ValueError:
        return False


@router.message()
async def handle_convert_amount_input(message: Message) -> None:
    """
    Handle numeric input when user has active convert panel.

    This allows users to type amounts directly instead of using buttons.
    Only activates when user has an active (non-expired) convert state.
    """
    if not message.text:
        return

    user_id = message.from_user.id if message.from_user else 0

    # Only handle if user has active convert panel
    if not has_active_state(user_id):
        return

    text = message.text.strip()

    # Only handle if it looks like a number
    if not _looks_like_number(text):
        return

    logger.debug(f"Convert amount input: user={user_id}, text={text}")

    state = get_user_state(user_id)
    state, error = set_amount(state, text)

    if error:
        await message.answer(f"❌ {error}")
        return

    state.last_result = None  # Clear result when amount changes
    save_user_state(user_id, state)

    # Send updated panel
    await message.answer(
        render_panel_text(state, None),
        reply_markup=get_convert_panel_keyboard(state, None),
        parse_mode="HTML",
    )
