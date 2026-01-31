"""Conversion tools: price, convert, unit."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.services.price_service import get_price_service
from armcalc.services.fx_service import get_fx_service
from armcalc.services.unit_service import get_unit_service
from armcalc.services.history_store import get_history_store
from armcalc.utils.logging import get_logger

logger = get_logger("tools_convert")
router = Router(name="tools_convert")


def parse_float(value: str) -> float | None:
    """Parse a float from string, handling commas."""
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


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

    Usage: /convert <amount> <from> <to>
    Example: /convert 100 usd amd
    """
    if not message.text:
        return

    parts = message.text.split()

    if len(parts) < 4:
        fx_service = get_fx_service()
        currencies = ", ".join(fx_service.get_supported_currencies()[:12])
        await message.answer(
            f"Usage: `/convert <amount> <from> <to>`\n"
            f"Example: `/convert 100 usd amd`\n\n"
            f"Supported: {currencies}...\n"
            f"Note: USDT = USD (stablecoin parity)",
            parse_mode="Markdown",
        )
        return

    amount = parse_float(parts[1])
    from_curr = parts[2].upper()
    to_curr = parts[3].upper()

    if amount is None:
        await message.answer("Invalid amount.", parse_mode="Markdown")
        return

    if amount <= 0:
        await message.answer("Amount must be positive.")
        return

    fx_service = get_fx_service()

    # Send typing indicator
    await message.bot.send_chat_action(message.chat.id, "typing")

    result = await fx_service.convert(amount, from_curr, to_curr)

    if result is None:
        await message.answer(
            f"Could not convert {from_curr} to {to_curr}.\n"
            f"Check currency codes and try again."
        )
        return

    result_text = (
        f"💱 **Currency Conversion**\n\n"
        f"{result.formatted}\n\n"
        f"Rate: 1 {from_curr} = {result.rate:.4f} {to_curr}"
    )

    # Save to history
    user_id = message.from_user.id if message.from_user else 0
    history = get_history_store()
    history.add_entry(
        user_id,
        f"{amount} {from_curr} -> {to_curr}",
        result.formatted,
        "convert",
    )

    await message.answer(result_text, parse_mode="Markdown")


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
