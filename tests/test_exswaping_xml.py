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
    CODE_ALIASES,
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

    def test_parse_usdttrc20_to_cashamd(self, xml_service, xml_content):
        """Test parsing USDTTRC20 -> CASHAMD direction."""
        directions = xml_service._parse_xml(xml_content)
        usdt_amd = [d for d in directions if d.from_code == "USDTTRC20" and d.to_code == "CASHAMD"]
        assert len(usdt_amd) == 1
        assert usdt_amd[0].rate == Decimal("385.00")

    def test_parse_cashamd_to_usdttrc20(self, xml_service, xml_content):
        """Test parsing CASHAMD -> USDTTRC20 direction."""
        directions = xml_service._parse_xml(xml_content)
        amd_usdt = [d for d in directions if d.from_code == "CASHAMD" and d.to_code == "USDTTRC20"]
        assert len(amd_usdt) == 1
        # Rate = 1 / 390
        expected_rate = Decimal("1") / Decimal("390")
        assert abs(amd_usdt[0].rate - expected_rate) < Decimal("0.0001")

    def test_parse_cashusd_to_usdttrc20(self, xml_service, xml_content):
        """Test parsing CASHUSD -> USDTTRC20 direction."""
        directions = xml_service._parse_xml(xml_content)
        usd_usdt = [d for d in directions if d.from_code == "CASHUSD" and d.to_code == "USDTTRC20"]
        assert len(usd_usdt) == 1
        assert usd_usdt[0].rate == Decimal("0.998")

    def test_parse_usdttrc20_to_sberbank_rub(self, xml_service, xml_content):
        """Test parsing USDTTRC20 -> Sberbank RUB direction."""
        directions = xml_service._parse_xml(xml_content)
        usdt_sber = [d for d in directions if d.from_code == "USDTTRC20" and d.method == "sberbank"]
        assert len(usdt_sber) >= 1
        assert usdt_sber[0].rate == Decimal("91.50")

    def test_parse_usdttrc20_to_tinkoff_rub(self, xml_service, xml_content):
        """Test parsing USDTTRC20 -> Tinkoff RUB direction."""
        directions = xml_service._parse_xml(xml_content)
        usdt_tink = [d for d in directions if d.from_code == "USDTTRC20" and d.method == "tinkoff"]
        assert len(usdt_tink) >= 1
        assert usdt_tink[0].rate == Decimal("91.00")

    def test_direction_rate_calculation(self):
        """Test ExchangeDirection rate calculation."""
        direction = ExchangeDirection(
            from_code="USDTTRC20",
            to_code="CASHAMD",
            from_name="Tether (TRC20)",
            to_name="Armenian Dram (Cash)",
            in_amount=Decimal("1"),
            out_amount=Decimal("385.00"),
        )
        assert direction.rate == Decimal("385.00")

    def test_direction_rate_with_different_in_amount(self):
        """Test rate calculation when in_amount != 1."""
        direction = ExchangeDirection(
            from_code="CASHAMD",
            to_code="USDTTRC20",
            from_name="Armenian Dram (Cash)",
            to_name="Tether (TRC20)",
            in_amount=Decimal("390"),
            out_amount=Decimal("1"),
        )
        expected = Decimal("1") / Decimal("390")
        assert abs(direction.rate - expected) < Decimal("0.0001")


class TestRateQuote:
    """Test RateQuote functionality."""

    def test_convert_simple(self):
        """Test simple conversion."""
        quote = RateQuote(
            from_code="USDTTRC20",
            to_code="CASHAMD",
            rate=Decimal("385.00"),
        )
        result = quote.convert(Decimal("100"))
        assert result == Decimal("38500.00")

    def test_convert_with_rounding(self):
        """Test conversion with rounding."""
        quote = RateQuote(
            from_code="CASHUSD",
            to_code="USDTTRC20",
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


class TestCodeNormalization:
    """Test code normalization (usdt -> USDTTRC20, etc.)."""

    def test_normalize_usdt(self, xml_service):
        """Test USDT normalizes to default unit."""
        assert xml_service.normalize_code("usdt") == "USDTTRC20"
        assert xml_service.normalize_code("USDT") == "USDTTRC20"

    def test_normalize_amd(self, xml_service):
        """Test AMD normalizes to default unit."""
        assert xml_service.normalize_code("amd") == "CASHAMD"
        assert xml_service.normalize_code("AMD") == "CASHAMD"

    def test_normalize_usd(self, xml_service):
        """Test USD normalizes to default unit."""
        assert xml_service.normalize_code("usd") == "CASHUSD"
        assert xml_service.normalize_code("USD") == "CASHUSD"

    def test_direct_codes_unchanged(self, xml_service):
        """Test specific codes are unchanged."""
        assert xml_service.normalize_code("USDTTRC20") == "USDTTRC20"
        assert xml_service.normalize_code("CASHAMD") == "CASHAMD"
        assert xml_service.normalize_code("CARDAMD") == "CARDAMD"


class TestDisplayNames:
    """Test display name generation."""

    def test_display_usdt_trc20(self, xml_service):
        """Test USDTTRC20 display name."""
        assert xml_service.get_display_name("USDTTRC20") == "USDT (TRC20)"

    def test_display_cashamd(self, xml_service):
        """Test CASHAMD display name."""
        assert xml_service.get_display_name("CASHAMD") == "AMD (Cash)"

    def test_display_sberrub(self, xml_service):
        """Test SBERRUB display name."""
        assert xml_service.get_display_name("SBERRUB") == "RUB (Sberbank)"

    def test_display_with_method(self, xml_service):
        """Test display name with method parameter."""
        assert xml_service.get_display_name("RUB", "tinkoff") == "RUB (Tinkoff)"


class TestXmlServiceAsync:
    """Test async XML service methods."""

    @pytest.mark.asyncio
    async def test_get_rate_usdt_to_amd(self, xml_service):
        """Test getting USDT -> AMD rate (uses normalization)."""
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999  # Far future
        xml_service._build_index()

        # User types "usdt amd" - should normalize to USDTTRC20 -> CASHAMD
        rate = await xml_service.get_rate("USDT", "AMD")
        assert rate is not None
        assert rate.from_code == "USDTTRC20"
        assert rate.to_code == "CASHAMD"
        assert rate.rate == Decimal("385.00")

    @pytest.mark.asyncio
    async def test_get_rate_amd_to_usdt(self, xml_service):
        """Test getting AMD -> USDT rate."""
        xml_content = Path("tests/fixtures/currencies.xml").read_text()
        xml_service._cache.directions = xml_service._parse_xml(xml_content)
        xml_service._cache.timestamp = 9999999999
        xml_service._build_index()

        rate = await xml_service.get_rate("AMD", "USDT")
        assert rate is not None
        assert rate.from_code == "CASHAMD"
        assert rate.to_code == "USDTTRC20"

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
        assert rate.rate == Decimal("91.50")

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
        assert rate.rate == Decimal("91.00")

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

        directions = await xml_service.list_directions(filter_from="USDTTRC20")
        assert len(directions) > 0
        assert all(d.from_code == "USDTTRC20" for d in directions)


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
