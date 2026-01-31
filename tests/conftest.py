"""Pytest configuration and fixtures."""

import os
import pytest

# Set test environment variables before importing modules
os.environ["BOT_TOKEN"] = "test_token_123:ABC"
os.environ["DRY_RUN"] = "true"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["HISTORY_DB_PATH"] = ":memory:"
os.environ["EXSWAPING_FIXTURE_PATH"] = "tests/fixtures/currencies.xml"


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment."""
    # Ensure we're in dry run mode for tests
    os.environ["DRY_RUN"] = "true"
    os.environ["EXSWAPING_FIXTURE_PATH"] = "tests/fixtures/currencies.xml"
    yield


@pytest.fixture
def reset_services():
    """Reset global service instances between tests."""
    # Reset XML service
    import armcalc.services.exswaping_xml_service as xml_mod
    xml_mod._xml_service = None

    # Reset FX service
    import armcalc.services.fx_service as fx_mod
    fx_mod._fx_service = None

    yield
