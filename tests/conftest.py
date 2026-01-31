"""Pytest configuration and fixtures."""

import os
import pytest

# Set test environment variables before importing modules
os.environ["BOT_TOKEN"] = "test_token_123:ABC"
os.environ["DRY_RUN"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["HISTORY_DB_PATH"] = ":memory:"


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment."""
    # Ensure we're in dry run mode for tests
    os.environ["DRY_RUN"] = "true"
    yield
