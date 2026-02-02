"""Bot setup and dispatcher configuration."""

import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from armcalc.config import get_settings
from armcalc.routers import get_all_routers
from armcalc.utils.logging import setup_logging, get_logger

logger = get_logger("bot")


def create_bot() -> Bot:
    """Create and configure the bot instance."""
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    return bot


def create_dispatcher() -> Dispatcher:
    """Create and configure the dispatcher with all routers."""
    dp = Dispatcher()

    # Register all routers
    routers = get_all_routers()
    for router in routers:
        dp.include_router(router)
        logger.debug(f"Registered router: {router.name}")

    logger.info(f"Registered {len(routers)} routers")

    return dp


async def on_startup(bot: Bot) -> None:
    """Startup handler."""
    settings = get_settings()
    mode = "DRY_RUN" if settings.dry_run else "LIVE"

    # Get bot info
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} (id={me.id}) in {mode} mode")


async def on_shutdown(bot: Bot) -> None:
    """Shutdown handler."""
    logger.info("Bot shutting down...")

    # Close service sessions
    from armcalc.services.price_service import get_price_service
    from armcalc.services.fx_service import get_fx_service

    await get_price_service().close()
    await get_fx_service().close()

    logger.info("Bot shutdown complete")


async def run_bot() -> None:
    """Run the bot with polling."""
    # Setup logging
    setup_logging()

    # Create bot and dispatcher
    bot = create_bot()
    dp = create_dispatcher()

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        # Start polling
        logger.info("Starting polling...")
        await dp.start_polling(
            bot,
            drop_pending_updates=True,
        )
    except Exception as e:
        logger.exception(f"Bot error: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(run_bot())
