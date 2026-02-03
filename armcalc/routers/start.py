"""Start command handler."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from armcalc.utils.logging import get_logger

logger = get_logger("start")
router = Router(name="start")

START_TEXT = """
Barev! 🤖 I'm <b>Armcalc</b> — calculator + exchange rates bot.

<b>━━━ 🧮 CALCULATOR ━━━</b>
Type any math expression:
• <code>2+2</code> • <code>100*5</code> • <code>sqrt(144)</code>
• <code>100+10%</code> • <code>sin(45)</code> • <code>2^10</code>

<b>━━━ 💱 EXCHANGE ━━━</b>
/convert — Interactive panel (recommended)
/convert 100 usdt amd — Quick convert
/rates — Current exchange rates
/pairs — Available networks/methods

<i>Defaults: USDT TRC20, AMD Cash, RUB Sberbank</i>

<b>━━━ 💰 CRYPTO ━━━</b>
/price btc — Bitcoin price
/price eth — Ethereum price

<b>━━━ 📋 ALL COMMANDS ━━━</b>
/start — This message
/help — Detailed help
/convert — Exchange panel
/rates — Exchange rates
/pairs — Available options
/price — Crypto prices
/keyboard — Calculator buttons
/history — Your history
/debug — Bot status
"""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user = message.from_user
    name = user.first_name if user else "there"

    logger.info(f"/start from {name} (id={user.id if user else 'unknown'})")

    text = START_TEXT.replace("Barev!", f"Barev {name}!")
    await message.answer(text, parse_mode="HTML")
