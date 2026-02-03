"""
Exswaping XML exchange rate service.

This service fetches and parses exchange rates from exswaping.com/currencies.xml

XML STRUCTURE ASSUMPTION (based on common exchange XML formats):
The XML is expected to have the following structure:

<rates>
  <item>
    <from>USDT</from>
    <to>AMD</to>
    <in>1</in>
    <out>402.50</out>
    <fromname>Tether USDT</fromname>
    <toname>Armenian Dram</toname>
    <minamount>10</minamount>
    <maxamount>10000</maxamount>
  </item>
  <item>
    <from>USDT</from>
    <to>SBERRUB</to>
    <in>1</in>
    <out>96.50</out>
    <fromname>Tether USDT</fromname>
    <toname>Sberbank RUB</toname>
    <method>sberbank</method>
  </item>
  ...
</rates>

If actual XML format differs, adjust the parsing logic accordingly.
Rate calculation: rate = out / in (how much 'to' you get per 'from')
"""

import asyncio
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import aiohttp

from armcalc.config import get_settings
from armcalc.utils.logging import get_logger

logger = get_logger("exswaping_xml")


@dataclass
class ExchangeDirection:
    """A single exchange direction from the XML."""

    from_code: str  # e.g., "USDT", "AMD", "USD"
    to_code: str  # e.g., "AMD", "USDT", "SBERRUB"
    from_name: str  # e.g., "Tether USDT"
    to_name: str  # e.g., "Armenian Dram"
    in_amount: Decimal  # Input amount for rate calculation
    out_amount: Decimal  # Output amount for rate calculation
    method: Optional[str] = None  # Payment method for RUB (sberbank, tinkoff, etc.)
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    city: Optional[str] = None  # City code (ERVN, LOSAN, etc.)

    @property
    def rate(self) -> Decimal:
        """Calculate rate: how much 'to' per 1 'from'."""
        if self.in_amount == 0:
            return Decimal("0")
        return self.out_amount / self.in_amount

    @property
    def normalized_to_code(self) -> str:
        """Get normalized to_code (extract currency from method codes)."""
        # Handle method-based codes like SBERRUB -> RUB
        code = self.to_code.upper()
        if code.endswith("RUB") and len(code) > 3:
            return "RUB"
        return code

    @property
    def display_to(self) -> str:
        """Get display string for destination."""
        if self.method:
            return f"RUB ({self.method.title()})"
        return self.to_code.upper()


@dataclass
class RateQuote:
    """A rate quote for conversion."""

    from_code: str  # XML code (e.g., USDTTRC20)
    to_code: str  # XML code (e.g., CASHAMD)
    rate: Decimal
    method: Optional[str] = None
    source: str = "xml"  # "xml" or "fallback"
    timestamp: float = 0.0
    from_display: str = ""  # User-friendly name
    to_display: str = ""  # User-friendly name

    def convert(self, amount: Decimal) -> Decimal:
        """Convert amount using this rate."""
        return (amount * self.rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def display_from(self) -> str:
        """Get display name for source."""
        return self.from_display or self.from_code

    @property
    def display_to(self) -> str:
        """Get display name for target."""
        if self.method:
            return f"RUB ({self.method.title()})"
        return self.to_display or self.to_code


@dataclass
class XmlCache:
    """Cached XML data."""

    directions: List[ExchangeDirection] = field(default_factory=list)
    timestamp: float = 0.0
    last_fetch_error: Optional[str] = None


# Method aliases for RUB payment methods
RUB_METHOD_ALIASES: Dict[str, str] = {
    "sber": "sberbank",
    "sberbank": "sberbank",
    "tink": "tinkoff",
    "tinkoff": "tinkoff",
    "alfa": "alfabank",
    "alfabank": "alfabank",
    "alpha": "alfabank",
    "vtb": "vtb",
    "raif": "raiffeisen",
    "raiffeisen": "raiffeisen",
    "qiwi": "qiwi",
    "yoomoney": "yoomoney",
    "yandex": "yoomoney",
}

# Method to XML code mapping (how methods appear in XML to_code)
METHOD_TO_CODE: Dict[str, str] = {
    "sberbank": "SBERRUB",
    "tinkoff": "TCSBRUB",
    "alfabank": "ACRUB",
    "vtb": "VTBRUB",
    "raiffeisen": "RFRUB",
    "qiwi": "QWRUB",
    "yoomoney": "YAMRUB",
}

# User-friendly code to XML unit mapping
# Users can type "usdt" and we map to the default network
CODE_ALIASES: Dict[str, List[str]] = {
    # USDT variants
    "USDT": ["USDTTRC20", "USDTBEP20", "USDTERC20", "USDT"],
    "USDTTRC20": ["USDTTRC20"],
    "USDTBEP20": ["USDTBEP20"],
    "USDTERC20": ["USDTERC20"],
    # AMD variants
    "AMD": ["CASHAMD", "CARDAMD", "AMD"],
    "CASHAMD": ["CASHAMD"],
    "CARDAMD": ["CARDAMD"],
    # USD variants
    "USD": ["CASHUSD", "USD"],
    "CASHUSD": ["CASHUSD"],
    # RUB - handled via METHOD_TO_CODE
    "RUB": ["SBERRUB", "TCSBRUB", "ACRUB", "VTBRUB", "RUB"],
}


class ExswapingXmlService:
    """
    Service for fetching and parsing exchange rates from exswaping.com XML.

    Features:
    - Async XML fetching with caching
    - Rate lookup with method support for RUB
    - DRY_RUN mode uses fixture file
    - Fallback-aware (caller can use fx_service if not found)
    """

    def __init__(self):
        """Initialize the service."""
        self._cache = XmlCache()
        self._settings = get_settings()
        self._session: Optional[aiohttp.ClientSession] = None
        # Index for fast lookups: (from_code, to_code, method) -> direction
        self._direction_index: Dict[Tuple[str, str, Optional[str]], ExchangeDirection] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self._settings.request_timeout_sec)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache.directions:
            return False
        age = time.time() - self._cache.timestamp
        return age < self._settings.exswaping_xml_ttl_sec

    def _parse_xml(self, xml_content: str) -> List[ExchangeDirection]:
        """
        Parse XML content into exchange directions.

        Handles multiple possible XML formats:
        1. <rates><item>...</item></rates>
        2. <exchangers><exchanger>...</exchanger></exchangers>
        3. <items><item>...</item></items>
        """
        directions = []

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return directions

        # Try different possible container/item tag combinations
        item_tags = ["item", "exchanger", "direction", "rate", "row"]
        items = []

        for tag in item_tags:
            items = root.findall(f".//{tag}")
            if items:
                logger.debug(f"Found {len(items)} items using tag '{tag}'")
                break

        if not items:
            # Try direct children
            items = list(root)
            logger.debug(f"Using {len(items)} direct children")

        for item in items:
            try:
                direction = self._parse_item(item)
                if direction:
                    directions.append(direction)
            except Exception as e:
                logger.debug(f"Failed to parse item: {e}")
                continue

        logger.info(f"Parsed {len(directions)} exchange directions from XML")
        return directions

    def _parse_item(self, item: ET.Element) -> Optional[ExchangeDirection]:
        """Parse a single item element into ExchangeDirection."""
        # Try different field name variations
        from_code = self._get_text(item, ["from", "give", "from_currency", "source"])
        to_code = self._get_text(item, ["to", "get", "to_currency", "target", "receive"])

        if not from_code or not to_code:
            return None

        from_name = self._get_text(item, ["fromname", "from_name", "give_name", "source_name"]) or from_code
        to_name = self._get_text(item, ["toname", "to_name", "get_name", "target_name"]) or to_code

        # Parse amounts for rate calculation
        in_str = self._get_text(item, ["in", "in_amount", "give_amount", "amount_from"]) or "1"
        out_str = self._get_text(item, ["out", "out_amount", "get_amount", "amount_to"]) or "1"

        try:
            in_amount = Decimal(in_str.replace(",", ".").strip())
            out_amount = Decimal(out_str.replace(",", ".").strip())
        except Exception:
            in_amount = Decimal("1")
            out_amount = Decimal("1")

        # Parse optional fields
        method = self._get_text(item, ["method", "payment_method", "bank"])
        min_amount_str = self._get_text(item, ["minamount", "min_amount", "min"])
        max_amount_str = self._get_text(item, ["maxamount", "max_amount", "max"])

        min_amount = None
        max_amount = None
        if min_amount_str:
            try:
                min_amount = Decimal(min_amount_str.replace(",", "."))
            except Exception:
                pass
        if max_amount_str:
            try:
                max_amount = Decimal(max_amount_str.replace(",", "."))
            except Exception:
                pass

        # Detect method from to_code if not explicit
        if not method:
            to_upper = to_code.upper()
            for m, code in METHOD_TO_CODE.items():
                if to_upper == code or to_upper.endswith(code):
                    method = m
                    break

        # Parse city (for location-specific rates like CASHUSD)
        city = self._get_text(item, ["city", "location", "place"])

        return ExchangeDirection(
            from_code=from_code.upper(),
            to_code=to_code.upper(),
            from_name=from_name,
            to_name=to_name,
            in_amount=in_amount,
            out_amount=out_amount,
            method=method,
            min_amount=min_amount,
            max_amount=max_amount,
            city=city.upper() if city else None,
        )

    def _get_text(self, element: ET.Element, tag_options: List[str]) -> Optional[str]:
        """Get text from element trying multiple tag names."""
        for tag in tag_options:
            # Try as child element
            child = element.find(tag)
            if child is not None and child.text:
                return child.text.strip()
            # Try as attribute
            attr = element.get(tag)
            if attr:
                return attr.strip()
        return None

    def _build_index(self) -> None:
        """Build lookup index from cached directions."""
        self._direction_index.clear()
        for d in self._cache.directions:
            # Index by exact codes with city
            key = (d.from_code, d.to_code, d.method, d.city)
            self._direction_index[key] = d

            # Also index without city (first match wins for backwards compat)
            key_no_city = (d.from_code, d.to_code, d.method, None)
            if key_no_city not in self._direction_index:
                self._direction_index[key_no_city] = d

            # Also index by normalized to_code for RUB
            if d.normalized_to_code != d.to_code:
                key_norm = (d.from_code, d.normalized_to_code, d.method, d.city)
                if key_norm not in self._direction_index:
                    self._direction_index[key_norm] = d

    async def _fetch_xml(self) -> Optional[str]:
        """Fetch XML from URL or fixture."""
        settings = self._settings

        # DRY_RUN mode: use fixture
        if settings.dry_run:
            logger.info("[DRY_RUN] Loading XML from fixture")
            fixture_path = Path(settings.exswaping_fixture_path)
            if fixture_path.exists():
                return fixture_path.read_text(encoding="utf-8")
            else:
                logger.warning(f"Fixture not found: {fixture_path}")
                # Return embedded minimal fixture
                return self._get_embedded_fixture()

        # Live mode: fetch from URL
        url = settings.exswaping_xml_url
        retries = 0

        while retries < settings.max_retries:
            try:
                session = await self._get_session()
                headers = {
                    "User-Agent": "ArmcalcBot/2.1 (Telegram Bot)",
                    "Accept": "application/xml, text/xml, */*",
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:
                        wait_time = 2 ** retries
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        retries += 1
                        continue
                    else:
                        logger.error(f"XML fetch failed: HTTP {response.status}")
                        self._cache.last_fetch_error = f"HTTP {response.status}"
                        return None

            except asyncio.TimeoutError:
                logger.warning("XML fetch timeout")
                retries += 1
                await asyncio.sleep(2 ** retries)
            except aiohttp.ClientError as e:
                logger.error(f"XML fetch error: {e}")
                self._cache.last_fetch_error = str(e)
                return None
            except Exception as e:
                logger.exception(f"Unexpected error fetching XML: {e}")
                self._cache.last_fetch_error = str(e)
                return None

        return None

    def _get_embedded_fixture(self) -> str:
        """Return embedded minimal fixture for DRY_RUN when file not found."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<rates>
  <item>
    <from>USDT</from>
    <to>AMD</to>
    <in>1</in>
    <out>402.50</out>
    <fromname>Tether USDT</fromname>
    <toname>Armenian Dram</toname>
  </item>
  <item>
    <from>AMD</from>
    <to>USDT</to>
    <in>405</in>
    <out>1</out>
    <fromname>Armenian Dram</fromname>
    <toname>Tether USDT</toname>
  </item>
  <item>
    <from>USD</from>
    <to>USDT</to>
    <in>1</in>
    <out>0.998</out>
    <fromname>US Dollar</fromname>
    <toname>Tether USDT</toname>
  </item>
  <item>
    <from>USDT</from>
    <to>USD</to>
    <in>1</in>
    <out>0.995</out>
    <fromname>Tether USDT</fromname>
    <toname>US Dollar</toname>
  </item>
  <item>
    <from>USDT</from>
    <to>SBERRUB</to>
    <in>1</in>
    <out>96.50</out>
    <fromname>Tether USDT</fromname>
    <toname>Sberbank RUB</toname>
    <method>sberbank</method>
  </item>
  <item>
    <from>USDT</from>
    <to>TCSBRUB</to>
    <in>1</in>
    <out>96.00</out>
    <fromname>Tether USDT</fromname>
    <toname>Tinkoff RUB</toname>
    <method>tinkoff</method>
  </item>
</rates>"""

    async def refresh_cache(self) -> bool:
        """Force refresh the cache."""
        xml_content = await self._fetch_xml()
        if xml_content:
            directions = self._parse_xml(xml_content)
            if directions:
                self._cache.directions = directions
                self._cache.timestamp = time.time()
                self._cache.last_fetch_error = None
                self._build_index()
                return True
        return False

    async def ensure_cache(self) -> None:
        """Ensure cache is populated and valid."""
        if not self._is_cache_valid():
            await self.refresh_cache()

    def normalize_method(self, method: Optional[str]) -> Optional[str]:
        """Normalize a payment method alias to canonical form."""
        if not method:
            return None
        return RUB_METHOD_ALIASES.get(method.lower().strip())

    def normalize_code(self, code: str) -> str:
        """
        Normalize user-friendly code to XML unit.

        Maps: usdt -> USDTTRC20, amd -> CASHAMD, etc.
        """
        upper = code.upper().strip()
        settings = self._settings

        # Direct match - already normalized
        if upper in ("USDTTRC20", "USDTBEP20", "CASHAMD", "CARDAMD", "CASHUSD"):
            return upper

        # Map common names to default units
        if upper == "USDT":
            return settings.default_usdt_unit
        if upper == "AMD":
            return settings.default_amd_unit
        if upper == "USD":
            return settings.default_usd_unit

        return upper

    def get_display_name(self, xml_code: str, method: Optional[str] = None) -> str:
        """Get user-friendly display name for an XML code."""
        upper = xml_code.upper()

        # Handle RUB methods
        if method:
            return f"RUB ({method.title()})"
        if upper.endswith("RUB") and len(upper) > 3:
            for m, code in METHOD_TO_CODE.items():
                if upper == code:
                    return f"RUB ({m.title()})"
            return "RUB"

        # Handle USDT variants
        if upper.startswith("USDT"):
            network = upper[4:] if len(upper) > 4 else ""
            if network:
                return f"USDT ({network})"
            return "USDT"

        # Handle AMD variants
        if upper.endswith("AMD") and len(upper) > 3:
            variant = upper[:-3]  # CASH, CARD, etc.
            return f"AMD ({variant.title()})"

        # Handle USD variants
        if upper.endswith("USD") and len(upper) > 3:
            variant = upper[:-3]
            return f"USD ({variant.title()})"

        return upper

    async def get_rate(
        self,
        from_code: str,
        to_code: str,
        method: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Optional[RateQuote]:
        """
        Get exchange rate for a currency pair.

        Supports user-friendly codes like "usdt", "amd" which are
        normalized to XML codes like "USDTTRC20", "CASHAMD".

        Args:
            from_code: Source currency (e.g., "USDT", "AMD", "usdttrc20")
            to_code: Target currency (e.g., "AMD", "RUB", "cashamd")
            method: Optional payment method for RUB (e.g., "sberbank")
            city: Optional city code for location-specific rates (e.g., "ERVN", "LOSAN")

        Returns:
            RateQuote if found, None otherwise
        """
        await self.ensure_cache()

        # Normalize codes
        from_norm = self.normalize_code(from_code)
        to_norm = self.normalize_code(to_code)
        norm_method = self.normalize_method(method)
        norm_city = city.upper() if city else None

        # Get all possible variants to try
        from_variants = CODE_ALIASES.get(from_code.upper(), [from_norm])
        to_variants = CODE_ALIASES.get(to_code.upper(), [to_norm])

        # If to is RUB and method specified, handle specially
        if to_code.upper() == "RUB" and norm_method:
            method_code = METHOD_TO_CODE.get(norm_method, "")
            if method_code:
                to_variants = [method_code]

        # Try all combinations of from/to variants
        for from_var in from_variants:
            for to_var in to_variants:
                # Try with city first (if specified)
                if norm_city:
                    key = (from_var, to_var, norm_method, norm_city)
                    if key in self._direction_index:
                        d = self._direction_index[key]
                        return RateQuote(
                            from_code=from_var,
                            to_code=to_var,
                            rate=d.rate,
                            method=d.method or norm_method,
                            source="xml",
                            timestamp=time.time(),
                            from_display=self.get_display_name(from_var),
                            to_display=self.get_display_name(to_var, d.method or norm_method),
                        )

                # Try with method (no city)
                key = (from_var, to_var, norm_method, None)
                if key in self._direction_index:
                    d = self._direction_index[key]
                    return RateQuote(
                        from_code=from_var,
                        to_code=to_var,
                        rate=d.rate,
                        method=d.method or norm_method,
                        source="xml",
                        timestamp=time.time(),
                        from_display=self.get_display_name(from_var),
                        to_display=self.get_display_name(to_var, d.method or norm_method),
                    )

                # Try without method
                key = (from_var, to_var, None, None)
                if key in self._direction_index:
                    d = self._direction_index[key]
                    return RateQuote(
                        from_code=from_var,
                        to_code=to_var,
                        rate=d.rate,
                        method=d.method,
                        source="xml",
                        timestamp=time.time(),
                        from_display=self.get_display_name(from_var),
                        to_display=self.get_display_name(to_var, d.method),
                    )

        # If to is RUB without method, try default method
        if to_code.upper() == "RUB" and not norm_method:
            default_method = self._settings.default_rub_method
            return await self.get_rate(from_code, to_code, default_method)

        return None

    async def list_directions(
        self,
        filter_from: Optional[str] = None,
        filter_to: Optional[str] = None,
    ) -> List[ExchangeDirection]:
        """
        List available exchange directions.

        Args:
            filter_from: Filter by source currency
            filter_to: Filter by target currency

        Returns:
            List of matching directions
        """
        await self.ensure_cache()

        directions = self._cache.directions

        if filter_from:
            from_upper = filter_from.upper()
            directions = [d for d in directions if d.from_code == from_upper]

        if filter_to:
            to_upper = filter_to.upper()
            directions = [
                d for d in directions
                if d.to_code == to_upper or d.normalized_to_code == to_upper
            ]

        return directions

    async def get_available_targets(self, from_code: str) -> List[Tuple[str, Optional[str]]]:
        """
        Get available target currencies for a source.

        Returns list of (to_code, method) tuples.
        """
        directions = await self.list_directions(filter_from=from_code)
        targets = []
        for d in directions:
            if d.normalized_to_code == "RUB" and d.method:
                targets.append((d.normalized_to_code, d.method))
            else:
                targets.append((d.to_code, None))
        return list(set(targets))

    def get_cache_info(self) -> dict:
        """Get cache status for debugging."""
        return {
            "directions_count": len(self._cache.directions),
            "cache_age_sec": time.time() - self._cache.timestamp if self._cache.timestamp else None,
            "cache_valid": self._is_cache_valid(),
            "last_error": self._cache.last_fetch_error,
        }

    def is_xml_pair(self, from_code: str, to_code: str, method: Optional[str] = None) -> bool:
        """
        Check if this pair should use XML rates (priority pairs).

        Priority pairs:
        - AMD <-> USDT
        - USD <-> USDT
        - Any pair involving RUB with method
        """
        f = from_code.upper()
        t = to_code.upper()

        # AMD <-> USDT
        if (f == "AMD" and t == "USDT") or (f == "USDT" and t == "AMD"):
            return True

        # USD <-> USDT
        if (f == "USD" and t == "USDT") or (f == "USDT" and t == "USD"):
            return True

        # RUB with method
        if t == "RUB" or f == "RUB":
            return True

        # Check if it's a method code (SBERRUB, etc.)
        for code in METHOD_TO_CODE.values():
            if t == code or f == code:
                return True

        return False


# Global service instance
_xml_service: Optional[ExswapingXmlService] = None


def get_xml_service() -> ExswapingXmlService:
    """Get or create XML service instance."""
    global _xml_service
    if _xml_service is None:
        _xml_service = ExswapingXmlService()
    return _xml_service
