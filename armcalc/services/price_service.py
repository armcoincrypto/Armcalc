"""Cryptocurrency price service with caching."""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional

import aiohttp

from armcalc.config import get_settings
from armcalc.utils.logging import get_logger

logger = get_logger("price_service")


@dataclass
class CryptoPrice:
    """Cryptocurrency price data."""

    symbol: str
    name: str
    price_usd: float
    price_amd: Optional[float] = None
    change_24h: Optional[float] = None
    timestamp: float = 0.0

    @property
    def formatted_usd(self) -> str:
        """Format USD price."""
        if self.price_usd >= 1:
            return f"${self.price_usd:,.2f}"
        return f"${self.price_usd:.6f}"

    @property
    def formatted_amd(self) -> str:
        """Format AMD price."""
        if self.price_amd:
            return f"{self.price_amd:,.0f} AMD"
        return "N/A"


class PriceService:
    """
    Cryptocurrency price service using CoinGecko API.

    Features:
    - Caching with configurable TTL
    - Dry run mode for testing
    - Graceful error handling
    - Rate limit aware
    """

    COINGECKO_API = "https://api.coingecko.com/api/v3"

    # Symbol to CoinGecko ID mapping
    SYMBOL_MAP = {
        "btc": "bitcoin",
        "eth": "ethereum",
        "sol": "solana",
        "bnb": "binancecoin",
        "xrp": "ripple",
        "ada": "cardano",
        "doge": "dogecoin",
        "dot": "polkadot",
        "matic": "matic-network",
        "shib": "shiba-inu",
        "ltc": "litecoin",
        "link": "chainlink",
        "uni": "uniswap",
        "avax": "avalanche-2",
        "atom": "cosmos",
        "xlm": "stellar",
        "etc": "ethereum-classic",
        "xmr": "monero",
        "trx": "tron",
        "usdt": "tether",
        "usdc": "usd-coin",
    }

    # Mock data for dry run mode
    MOCK_PRICES = {
        "bitcoin": CryptoPrice("BTC", "Bitcoin", 43250.00, 17300000, -1.2),
        "ethereum": CryptoPrice("ETH", "Ethereum", 2650.00, 1060000, 2.5),
        "solana": CryptoPrice("SOL", "Solana", 98.50, 39400, 5.1),
        "dogecoin": CryptoPrice("DOGE", "Dogecoin", 0.085, 34, -0.8),
    }

    def __init__(self):
        """Initialize the price service."""
        self._cache: Dict[str, CryptoPrice] = {}
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

    def _is_cache_valid(self, coin_id: str) -> bool:
        """Check if cached price is still valid."""
        if coin_id not in self._cache:
            return False
        cached = self._cache[coin_id]
        age = time.time() - cached.timestamp
        return age < self._settings.price_cache_ttl_sec

    def _get_coin_id(self, symbol: str) -> Optional[str]:
        """Convert symbol to CoinGecko coin ID."""
        symbol_lower = symbol.lower().strip()
        return self.SYMBOL_MAP.get(symbol_lower, symbol_lower)

    async def _fetch_price(self, coin_id: str) -> Optional[CryptoPrice]:
        """Fetch price from CoinGecko API."""
        settings = self._settings

        # Dry run mode
        if settings.dry_run:
            logger.info(f"[DRY_RUN] Would fetch price for {coin_id}")
            mock = self.MOCK_PRICES.get(coin_id)
            if mock:
                mock.timestamp = time.time()
                return mock
            # Return generic mock for unknown coins
            return CryptoPrice(
                symbol=coin_id.upper()[:5],
                name=coin_id.title(),
                price_usd=100.00,
                price_amd=40000,
                change_24h=0.0,
                timestamp=time.time(),
            )

        url = f"{self.COINGECKO_API}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd,amd",
            "include_24hr_change": "true",
        }

        retries = 0
        max_retries = settings.max_retries

        while retries < max_retries:
            try:
                session = await self._get_session()
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        # Rate limited
                        wait_time = 2 ** retries
                        logger.warning(f"Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        retries += 1
                        continue

                    if response.status != 200:
                        logger.error(f"API error: {response.status}")
                        return None

                    data = await response.json()

                    if coin_id not in data:
                        logger.warning(f"Coin not found: {coin_id}")
                        return None

                    coin_data = data[coin_id]
                    price = CryptoPrice(
                        symbol=coin_id.upper()[:5],
                        name=coin_id.replace("-", " ").title(),
                        price_usd=coin_data.get("usd", 0),
                        price_amd=coin_data.get("amd"),
                        change_24h=coin_data.get("usd_24h_change"),
                        timestamp=time.time(),
                    )
                    return price

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching price for {coin_id}")
                retries += 1
                await asyncio.sleep(2 ** retries)
            except aiohttp.ClientError as e:
                logger.error(f"Client error: {e}")
                retries += 1
                await asyncio.sleep(2 ** retries)
            except Exception as e:
                logger.exception(f"Unexpected error fetching {coin_id}: {e}")
                return None

        return None

    async def get_price(self, symbol: str) -> Optional[CryptoPrice]:
        """
        Get cryptocurrency price.

        Args:
            symbol: Cryptocurrency symbol (e.g., 'btc', 'eth')

        Returns:
            CryptoPrice object or None if not found
        """
        coin_id = self._get_coin_id(symbol)
        if not coin_id:
            return None

        # Check cache
        if self._is_cache_valid(coin_id):
            logger.debug(f"Cache hit for {coin_id}")
            return self._cache[coin_id]

        # Fetch fresh price
        price = await self._fetch_price(coin_id)
        if price:
            self._cache[coin_id] = price

        return price

    def get_supported_symbols(self) -> list:
        """Get list of supported cryptocurrency symbols."""
        return sorted(self.SYMBOL_MAP.keys())


# Global service instance
_price_service: Optional[PriceService] = None


def get_price_service() -> PriceService:
    """Get or create price service instance."""
    global _price_service
    if _price_service is None:
        _price_service = PriceService()
    return _price_service
