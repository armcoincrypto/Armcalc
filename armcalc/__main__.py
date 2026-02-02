"""Entry point for running the bot as a module."""

import asyncio
from armcalc.bot import run_bot

if __name__ == "__main__":
    asyncio.run(run_bot())
