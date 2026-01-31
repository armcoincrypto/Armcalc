"""Help command handler."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.utils.logging import get_logger

logger = get_logger("help")
router = Router(name="help")

HELP_TEXT = """
🧮 **Armcalc Bot**

**Calculator**
• `2 + 2` → 4
• `100 + 10%` → 110
• `sqrt(16)` → 4
• `sin(90)` → 1
• `pow(2, 10)` → 1024

**Crypto**
• `/price btc` - Bitcoin
• `/price eth` - Ethereum

**Convert**
• `/convert 100 usdt amd`
• `/convert 100 amd usdt`
• `/convert 100 usdt sberbank rub`
• `/convert 100 usdt tinkoff rub`

**Other**
• `/history` - Last calculations
• `/keyboard` - Calculator buttons
• `/help` - This message
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    logger.info(f"/help from user {message.from_user.id if message.from_user else 'unknown'}")
    await message.answer(HELP_TEXT, parse_mode="Markdown")
