"""Start command handler."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from armcalc.utils.logging import get_logger

logger = get_logger("start")
router = Router(name="start")

START_TEXT = """
Barev! 🤖 I'm <b>Armcalc</b>

<b>🧮 Calculator</b>
Just type any math expression:
• <code>2+2</code> → 4
• <code>100+10%</code> → 110
• <code>sqrt(16)</code> → 4
• <code>sin(90)</code> → 1
• <code>pow(2,10)</code> → 1024

<b>💱 Currency</b>
/convert 100 usdt amd
/convert 100 amd usdt
/convert 100 usdt sberbank rub
/convert 100 usdt tinkoff rub

<b>📊 Rates</b>
/rates - Current exchange rates

<b>💰 Crypto</b>
/price btc - Bitcoin price
/price eth - Ethereum price

<b>📋 Other</b>
/history - Your calculations
/keyboard - Calculator buttons
/help - All commands
"""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user = message.from_user
    name = user.first_name if user else "there"

    logger.info(f"/start from {name} (id={user.id if user else 'unknown'})")

    text = START_TEXT.replace("Barev!", f"Barev {name}!")
    await message.answer(text, parse_mode="HTML")
