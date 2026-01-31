"""Foreign exchange rate service with caching."""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import aiohttp

from armcalc.config import get_settings
from armcalc.utils.logging import get_logger

logger = get_logger("fx_service")


@dataclass
class ConversionResult:
    """Currency conversion result."""

    amount: float
    from_currency: str
    to_currency: str
    result: float
    rate: float
    timestamp: float = 0.0

    @property
    def formatted(self) -> str:
        """Format the conversion result."""
        # Determine decimal places based on currency
        if self.to_currency.upper() in ("AMD", "RUB", "JPY", "KRW"):
            result_str = f"{self.result:,.0f}"
        else:
            result_str = f"{self.result:,.2f}"

        if self.from_currency.upper() in ("AMD", "RUB", "JPY", "KRW"):
            amount_str = f"{self.amount:,.0f}"
        else:
            amount_str = f"{self.amount:,.2f}"

        return f"{amount_str} {self.from_currency.upper()} = {result_str} {self.to_currency.upper()}"


class FxService:
    """
    Foreign exchange service using exchangerate.host API.

    Features:
    - Caching with configurable TTL
    - Dry run mode for testing
    - USDT treated as USD parity
    - Support for common currencies
    """

    # Free API endpoint (no key required)
    FX_API = "https://api.exchangerate.host/latest"
    FX_API_FALLBACK = "https://open.er-api.com/v6/latest"

    # Supported currencies
    SUPPORTED_CURRENCIES = {
        "USD", "EUR", "GBP", "RUB", "AMD", "AED", "TRY", "GEL",
        "JPY", "CNY", "KRW", "INR", "CAD", "AUD", "CHF", "PLN",
    }

    # USDT is treated as USD
    STABLECOIN_PARITY = {
        "USDT": "USD",
        "USDC": "USD",
        "BUSD": "USD",
        "DAI": "USD",
    }

    # Mock rates for dry run (rates relative to USD)
    MOCK_RATES = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "RUB": 89.5,
        "AMD": 405.0,
        "AED": 3.67,
        "TRY": 30.5,
        "GEL": 2.65,
        "JPY": 148.5,
        "CNY": 7.24,
        "KRW": 1320.0,
        "INR": 83.1,
        "CAD": 1.35,
        "AUD": 1.53,
        "CHF": 0.88,
        "PLN": 4.02,
    }

    def __init__(self):
        """Initialize the FX service."""
        self._cache: Dict[str, Tuple[Dict[str, float], float]] = {}
        self._settings = get_settings()
        self._session: Optional[aiohttp.ClientSession] = None

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

    def _normalize_currency(self, currency: str) -> str:
        """Normalize currency code."""
        upper = currency.upper().strip()
        # Handle stablecoins
        if upper in self.STABLECOIN_PARITY:
            return self.STABLECOIN_PARITY[upper]
        return upper

    def _is_cache_valid(self, base: str) -> bool:
        """Check if cached rates are still valid."""
        if base not in self._cache:
            return False
        _, timestamp = self._cache[base]
        age = time.time() - timestamp
        return age < self._settings.fx_cache_ttl_sec

    async def _fetch_rates(self, base: str) -> Optional[Dict[str, float]]:
        """Fetch exchange rates from API."""
        settings = self._settings

        # Dry run mode
        if settings.dry_run:
            logger.info(f"[DRY_RUN] Would fetch rates for {base}")
            # Convert mock rates to be relative to the requested base
            if base not in self.MOCK_RATES:
                return None
            base_rate = self.MOCK_RATES[base]
            rates = {k: v / base_rate for k, v in self.MOCK_RATES.items()}
            return rates

        # Try primary API
        urls = [
            (self.FX_API, {"base": base}),
            (f"{self.FX_API_FALLBACK}/{base}", {}),
        ]

        for url, params in urls:
            retries = 0
            while retries < settings.max_retries:
                try:
                    session = await self._get_session()
                    async with session.get(url, params=params if params else None) as response:
                        if response.status == 429:
                            wait_time = 2 ** retries
                            logger.warning(f"Rate limited, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            retries += 1
                            continue

                        if response.status != 200:
                            logger.warning(f"API error {response.status} from {url}")
                            break  # Try next API

                        data = await response.json()

                        # Handle different API response formats
                        if "rates" in data:
                            return data["rates"]
                        elif "conversion_rates" in data:
                            return data["conversion_rates"]

                        logger.warning(f"Unexpected response format from {url}")
                        break

                except asyncio.TimeoutError:
                    logger.warning(f"Timeout fetching rates from {url}")
                    retries += 1
                    await asyncio.sleep(2 ** retries)
                except aiohttp.ClientError as e:
                    logger.error(f"Client error from {url}: {e}")
                    break
                except Exception as e:
                    logger.exception(f"Unexpected error from {url}: {e}")
                    break

        return None

    async def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> Optional[ConversionResult]:
        """
        Convert amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            ConversionResult or None if conversion failed
        """
        from_curr = self._normalize_currency(from_currency)
        to_curr = self._normalize_currency(to_currency)

        if from_curr == to_curr:
            return ConversionResult(
                amount=amount,
                from_currency=from_currency,
                to_currency=to_currency,
                result=amount,
                rate=1.0,
                timestamp=time.time(),
            )

        # Check cache
        if self._is_cache_valid(from_curr):
            rates, timestamp = self._cache[from_curr]
        else:
            rates = await self._fetch_rates(from_curr)
            if rates:
                self._cache[from_curr] = (rates, time.time())
            else:
                return None

        if to_curr not in rates:
            logger.warning(f"Currency not found: {to_curr}")
            return None

        rate = rates[to_curr]
        result = amount * rate

        return ConversionResult(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            result=result,
            rate=rate,
            timestamp=time.time(),
        )

    async def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between two currencies."""
        result = await self.convert(1.0, from_currency, to_currency)
        return result.rate if result else None

    def get_supported_currencies(self) -> list:
        """Get list of supported currencies."""
        all_currencies = set(self.SUPPORTED_CURRENCIES)
        all_currencies.update(self.STABLECOIN_PARITY.keys())
        return sorted(all_currencies)


# Global service instance
_fx_service: Optional[FxService] = None


def get_fx_service() -> FxService:
    """Get or create FX service instance."""
    global _fx_service
    if _fx_service is None:
        _fx_service = FxService()
    return _fx_service
