"""Start command handler."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from armcalc.utils.logging import get_logger

logger = get_logger("start")
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Handle /start command.

    Sends Armenian greeting and brief instructions.
    """
    user = message.from_user
    name = user.first_name if user else "there"

    logger.info(f"/start from {name} (id={user.id if user else 'unknown'})")

    await message.answer(
        f"Barev {name}! 🤖\n\n"
        "I'm Armcalc - your calculator bot!\n\n"
        "• Math: `2+2`, `100+10%`\n"
        "• Scientific: `sqrt(16)`, `sin(90)`\n"
        "• Crypto: /price btc\n"
        "• Currency: /convert 100 usd amd\n"
        "• Units: /unit 10 km miles\n\n"
        "Use /help for all commands."
    )
