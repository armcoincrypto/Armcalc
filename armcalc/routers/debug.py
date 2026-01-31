"""Debug command for bot status."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.config import get_settings
from armcalc.utils.logging import get_logger

logger = get_logger("debug")
router = Router(name="debug")


@router.message(Command("debug", "status"))
async def cmd_debug(message: Message) -> None:
    """
    Show debug information.

    Displays non-sensitive configuration values.
    """
    settings = get_settings()
    info = settings.get_debug_info()

    lines = [
        "🔧 **Armcalc Debug Info**\n",
        f"Version: {info['version']}",
        f"Python: {info['python_version']}",
        f"Mode: {info['mode']}",
        f"Log Level: {info['log_level']}",
        "",
        "**Cache TTLs:**",
        f"  Price: {info['price_cache_ttl_sec']}s",
        f"  FX: {info['fx_cache_ttl_sec']}s",
        "",
        "**Settings:**",
        f"  Timeout: {info['request_timeout_sec']}s",
        f"  Timezone: {info['timezone']}",
        f"  DB: {info['history_db_path']}",
        "",
        f"Token: {info['bot_token']} (masked)",
    ]

    await message.answer("\n".join(lines), parse_mode="Markdown")
