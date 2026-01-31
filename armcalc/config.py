"""Configuration management using pydantic-settings."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Bot configuration
    bot_token: str = Field(..., description="Telegram Bot Token")

    # Mode
    dry_run: bool = Field(default=False, description="Enable dry run mode for API calls")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Cache TTLs (seconds)
    price_cache_ttl_sec: int = Field(default=60, description="Crypto price cache TTL")
    fx_cache_ttl_sec: int = Field(default=900, description="FX rate cache TTL (15 min)")

    # HTTP settings
    request_timeout_sec: int = Field(default=10, description="HTTP request timeout")
    max_retries: int = Field(default=3, description="Max retries for HTTP requests")

    # Database
    history_db_path: str = Field(
        default="./data/history.sqlite3",
        description="Path to SQLite history database"
    )

    # Defaults
    default_fiat: str = Field(default="USD", description="Default fiat currency")
    default_crypto_fiat: str = Field(default="USD", description="Default crypto quote currency")

    # Timezone
    timezone: str = Field(default="Asia/Yerevan", description="Default timezone")

    # History
    history_limit: int = Field(default=10, description="Max history entries to show")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return upper

    @field_validator("history_db_path")
    @classmethod
    def ensure_db_directory(cls, v: str) -> str:
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)

    def get_masked_token(self) -> str:
        """Return masked bot token for logging."""
        if len(self.bot_token) > 10:
            return f"{self.bot_token[:4]}...{self.bot_token[-4:]}"
        return "****"

    def get_debug_info(self) -> dict:
        """Return non-sensitive config info for /debug command."""
        import sys
        return {
            "version": "2.0.0",
            "python_version": sys.version.split()[0],
            "mode": "DRY_RUN" if self.dry_run else "LIVE",
            "log_level": self.log_level,
            "price_cache_ttl_sec": self.price_cache_ttl_sec,
            "fx_cache_ttl_sec": self.fx_cache_ttl_sec,
            "request_timeout_sec": self.request_timeout_sec,
            "history_db_path": self.history_db_path,
            "timezone": self.timezone,
            "bot_token": self.get_masked_token(),
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
