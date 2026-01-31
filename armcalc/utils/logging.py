"""Logging configuration."""

import logging
import sys
from typing import Optional

from armcalc.config import get_settings


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configure and return the root logger."""
    settings = get_settings()
    log_level = level or settings.log_level

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Get logger for armcalc
    logger = logging.getLogger("armcalc")
    logger.setLevel(getattr(logging, log_level))

    # Log startup info
    mode = "DRY_RUN" if settings.dry_run else "LIVE"
    logger.info(f"Armcalc v2.0.0 starting in {mode} mode")
    logger.info(f"Log level: {log_level}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(f"armcalc.{name}")
