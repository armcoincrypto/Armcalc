#!/usr/bin/env python3
"""Main entry point for Armcalc bot."""

import asyncio
import sys

from armcalc.bot import run_bot


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
