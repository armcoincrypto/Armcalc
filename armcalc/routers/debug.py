"""Debug command for bot status."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from armcalc.config import get_settings
from armcalc.services.exswaping_xml_service import get_xml_service
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

    # Get XML cache info
    xml_service = get_xml_service()
    xml_cache = xml_service.get_cache_info()

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
        f"  XML: {info['exswaping_xml_ttl_sec']}s",
        "",
        "**XML Service:**",
        f"  URL: {info['exswaping_xml_url']}",
        f"  Directions: {xml_cache['directions_count']}",
        f"  Cache valid: {xml_cache['cache_valid']}",
        f"  Cache age: {xml_cache['cache_age_sec']:.0f}s" if xml_cache['cache_age_sec'] else "  Cache age: N/A",
        f"  Default RUB: {info['default_rub_method']}",
    ]

    if xml_cache['last_error']:
        lines.append(f"  Last error: {xml_cache['last_error']}")

    lines.extend([
        "",
        "**Settings:**",
        f"  Timeout: {info['request_timeout_sec']}s",
        f"  Timezone: {info['timezone']}",
        f"  DB: {info['history_db_path']}",
        "",
        f"Token: {info['bot_token']} (masked)",
    ])

    await message.answer("\n".join(lines), parse_mode="Markdown")
