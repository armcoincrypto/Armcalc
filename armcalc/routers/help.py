"""Help command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.utils.logging import get_logger

logger = get_logger("help")
router = Router(name="help")

HELP_TEXT = """
<b>🧮 Calculator</b>
Just type any math:
• <code>2+2</code> → 4
• <code>100+10%</code> → 110
• <code>sqrt(16)</code> → 4
• <code>pow(2,10)</code> → 1024

<b>💱 Currency Conversion</b>
/convert 100 usdt amd
/convert 100 amd usdt
/convert 100 usdt sberbank rub

<b>Defaults:</b>
• USDT → TRC20 network
• AMD → Cash
• RUB → Sberbank
<i>Use /pairs to see other options</i>

<b>📊 Rates &amp; Pairs</b>
/rates - Current exchange rates
/pairs - Available networks/methods
/pairs usdt - USDT options

<b>💰 Crypto Prices</b>
/price btc - Bitcoin
/price eth - Ethereum

<b>📋 Other</b>
/history - Recent calculations
/keyboard - Calculator keyboard
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    logger.info(f"/help from user {message.from_user.id if message.from_user else 'unknown'}")
    await message.answer(HELP_TEXT, parse_mode="HTML")
