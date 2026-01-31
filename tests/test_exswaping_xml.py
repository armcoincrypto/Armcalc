"""Tests for exswaping XML service."""

import os
from decimal import Decimal
from pathlib import Path

import pytest

# Set test environment before imports
os.environ["BOT_TOKEN"] = "test_token_123:ABC"
os.environ["DRY_RUN"] = "true"
os.environ["EXSWAPING_FIXTURE_PATH"] = "tests/fixtures/currencies.xml"

from armcalc.services.exswaping_xml_service import (
    ExswapingXmlService,
    ExchangeDirection,
    RateQuote,
    RUB_METHOD_ALIASES,
)


@pytest.fixture
def xml_content():
    """Load test XML fixture."""
    fixture_path = Path("tests/fixtures/currencies.xml")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def xml_service():
    """Create a fresh XML service instance."""
    # Reset global instance
    import armcalc.services.exswaping_xml_service as mod
    mod._xml_service = None
    return ExswapingXmlService()


class TestXmlParsing:
    """Test XML parsing functionality."""

    def test_parse_xml_creates_directions(self, xml_service, xml_content):
        """Test that XML is parsed into directions."""
        directions = xml_service._parse_xml(xml_content)
        assert len(directions) > 0

    def test_parse_usdt_to_amd(self, xml_service, xml_content):
        """Test parsing USDT -> AMD direction."""
        directions = xml_service._parse_xml(xml_content)
        usdt_amd = [d for d in directions if d.from_code == "USDT" and d.to_code == "AMD"]
        assert len(usdt_amd) == 1
        assert usdt_amd[0].rate == Decimal("402.50")

    def test_parse_amd_to_usdt(self, xml_service, xml_content):
        """Test parsing AMD -> USDT direction."""
        directions = xml_service._parse_xml(xml_content)
        amd_usdt = [d for d in directions if d.from_code == "AMD" and d.to_code == "USDT"]
        assert len(amd_usdt) == 1
        # Rate = 1 / 405
        expected_rate = Decimal("1") / Decimal("405")
        assert abs(amd_usdt[0].rate - expected_rate) < Decimal("0.0001")

    def test_parse_usd_to_usdt(self, xml_service, xml_content):
        """Test parsing USD -> USDT direction."""
        directions = xml_service._parse_xml(xml_content)
        usd_usdt = [d for d in directions if d.from_code == "USD" and d.to_code == "USDT"]
        assert len(usd_usdt) == 1
        assert usd_usdt[0].rate == Decimal("0.998")

    def test_parse_usdt_to_sberbank_rub(self, xml_service, xml_content):
        """Test parsing USDT -> Sberbank RUB direction."""
        directions = xml_service._parse_xml(xml_content)
        usdt_sber = [d for d in directions if d.from_code == "USDT" and d.method == "sberbank"]
        assert len(usdt_sber) >= 1
        assert usdt_sber[0].rate == Decimal("96.50")

    def test_parse_usdt_to_tinkoff_rub(self, xml_service, xml_content):
        """Test parsing USDT -> Tinkoff RUB direction."""
        directions = xml_service._parse_xml(xml_content)
        usdt_tink = [d for d in directions if d.from_code == "USDT" and d.method == "tinkoff"]
        assert len(usdt_tink) >= 1
        assert usdt_tink[0].rate == Decimal("96.00")

    def test_direction_rate_calculation(self):
        """Test ExchangeDirection rate calculation."""
        direction = ExchangeDirection(
            from_code="USDT",
            to_code="AMD",
            from_name="Tether",
            to_name="Armenian Dram",
            in_amount=Decimal("1"),
            out_amount=Decimal("402.50"),
        )
        assert direction.rate == Decimal("402.50")

    def test_direction_rate_with_different_in_amount(self):
        """Test rate calculation when in_amount != 1."""
        direction = ExchangeDirection(
            from_code="AMD",
            to_code="USDT",
            from_name="Armenian Dram",
            to_name="Tether",
            in_amount=Decimal("405"),
            out_amount=Decimal("1"),
        )
        expected = Decimal("1") / Decimal("405")
        assert abs(direction.rate - expected) < Decimal("0.0001")


class TestRateQuote:
    """Test RateQuote functionality."""

    def test_convert_simple(self):
        """Test simple conversion."""
        quote = RateQuote(
            from_code="USDT",
            to_code="AMD",
            rate=Decimal("402.50"),
        )
        result = quote.convert(Decimal("100"))
        assert result == Decimal("40250.00")

    def test_convert_with_rounding(self):
        """Test conversion with rounding."""
        quote = RateQuote(
            from_code="USD",
            to_code="USDT",
            rate=Decimal("0.998"),
        )
        result = quote.convert(Decimal("100"))
        assert result == Decimal("99.80")


class TestMethodAliases:
    """Test RUB method aliases."""

    def test_sberbank_aliases(self):
        """Test Sberbank aliases."""
        assert RUB_METHOD_ALIASES["sber"] == "sberbank"
        assert RUB_METHOD_ALIASES["sberbank"] == "sberbank"

    def test_tinkoff_aliases(self):
        """Test Tinkoff aliases."""
        assert RUB_METHOD_ALIASES["tink"] == "tinkoff"
        assert RUB_METHOD_ALIASES["tinkoff"] == "tinkoff"

    def test_alfabank_aliases(self):
        """Test Alfabank aliases."""
        assert RUB_METHOD_ALIASES["alfa"] == "alfabank"
        assert RUB_METHOD_ALIASES["alpha"] == "alfabank"


class TestXmlServiceAsync:
    """Test async XML service methods."""

    @pytest.mark.asyncio
    async def test_get_rate_usdt_to_amd(self, xml_service):
        """Test getting USDT -> AMD rate."""
        # Load fixture
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999  # Far future
        xml_service._build_index()

        rate = await xml_service.get_rate("USDT", "AMD")
        assert rate is not None
        assert rate.from_code == "USDT"
        assert rate.to_code == "AMD"
        assert rate.rate == Decimal("402.50")

    @pytest.mark.asyncio
    async def test_get_rate_amd_to_usdt(self, xml_service):
        """Test getting AMD -> USDT rate."""
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999
        xml_service._build_index()

        rate = await xml_service.get_rate("AMD", "USDT")
        assert rate is not None
        assert rate.from_code == "AMD"
        assert rate.to_code == "USDT"

    @pytest.mark.asyncio
    async def test_get_rate_usdt_to_rub_sberbank(self, xml_service):
        """Test getting USDT -> RUB (Sberbank) rate."""
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999
        xml_service._build_index()

        rate = await xml_service.get_rate("USDT", "RUB", "sberbank")
        assert rate is not None
        assert rate.method == "sberbank"
        assert rate.rate == Decimal("96.50")

    @pytest.mark.asyncio
    async def test_get_rate_usdt_to_rub_tinkoff(self, xml_service):
        """Test getting USDT -> RUB (Tinkoff) rate."""
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999
        xml_service._build_index()

        rate = await xml_service.get_rate("USDT", "RUB", "tinkoff")
        assert rate is not None
        assert rate.method == "tinkoff"
        assert rate.rate == Decimal("96.00")

    @pytest.mark.asyncio
    async def test_list_directions_all(self, xml_service):
        """Test listing all directions."""
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999
        xml_service._build_index()

        directions = await xml_service.list_directions()
        assert len(directions) > 0

    @pytest.mark.asyncio
    async def test_list_directions_filtered(self, xml_service):
        """Test listing directions filtered by from currency."""
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999
        xml_service._build_index()

        directions = await xml_service.list_directions(filter_from="USDT")
        assert len(directions) > 0
        assert all(d.from_code == "USDT" for d in directions)


class TestIsXmlPair:
    """Test is_xml_pair detection."""

    def test_amd_usdt_is_xml_pair(self, xml_service):
        """Test AMD -> USDT is detected as XML pair."""
        assert xml_service.is_xml_pair("AMD", "USDT") is True
        assert xml_service.is_xml_pair("USDT", "AMD") is True

    def test_usd_usdt_is_xml_pair(self, xml_service):
        """Test USD -> USDT is detected as XML pair."""
        assert xml_service.is_xml_pair("USD", "USDT") is True
        assert xml_service.is_xml_pair("USDT", "USD") is True

    def test_rub_is_xml_pair(self, xml_service):
        """Test RUB directions are detected as XML pair."""
        assert xml_service.is_xml_pair("USDT", "RUB") is True
        assert xml_service.is_xml_pair("RUB", "USDT") is True

    def test_eur_usd_is_not_xml_pair(self, xml_service):
        """Test EUR -> USD is not detected as XML pair."""
        assert xml_service.is_xml_pair("EUR", "USD") is False

    def test_gbp_amd_is_not_xml_pair(self, xml_service):
        """Test GBP -> AMD is not detected as XML pair."""
        assert xml_service.is_xml_pair("GBP", "AMD") is False
