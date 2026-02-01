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
Just type math: <code>2+2</code>, <code>sqrt(16)</code>, <code>100+10%</code>

<b>💱 Currency</b>
/convert 100 usdt amd
/convert 100 usdt sberbank rub
/pairs - See available options

<i>Defaults: USDT=TRC20, AMD=Cash, RUB=Sberbank</i>

<b>📊 Rates</b>
/rates - Current exchange rates

<b>💰 Crypto</b>
/price btc, /price eth

<b>📋 Other</b>
/history, /keyboard, /help
"""


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user = message.from_user
    name = user.first_name if user else "there"

    logger.info(f"/start from {name} (id={user.id if user else 'unknown'})")

    text = START_TEXT.replace("Barev!", f"Barev {name}!")
    await message.answer(text, parse_mode="HTML")
