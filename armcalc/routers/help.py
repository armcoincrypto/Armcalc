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
• <code>sin(90)</code> → 1
• <code>cos(0)</code> → 1
• <code>tan(45)</code> → 1
• <code>log(100)</code> → 2
• <code>pow(2,10)</code> → 1024
• <code>pi</code> → 3.14159
• <code>e</code> → 2.71828

<b>💱 Currency Conversion</b>
/convert 100 usdt amd
/convert 100 amd usdt
/convert 100 usdt sberbank rub
/convert 100 usdt tinkoff rub

<b>📊 Exchange Rates</b>
/rates - Show current rates

<b>💰 Crypto Prices</b>
/price btc - Bitcoin
/price eth - Ethereum
/price sol - Solana

<b>📋 Other</b>
/history - Your last calculations
/keyboard - Calculator keyboard
/help - This message
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    logger.info(f"/help from user {message.from_user.id if message.from_user else 'unknown'}")
    await message.answer(HELP_TEXT, parse_mode="HTML")
