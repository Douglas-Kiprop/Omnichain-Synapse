import aiohttp
from typing import Any, Dict, List, Optional
from .base import BaseClient
import logging

logger = logging.getLogger(__name__)

class AsyncBinanceClient(BaseClient):
    """
    Asynchronous client for Binance public API.
    Provides accurate OHLCV klines and spot prices using Binance symbols (e.g., 'BTC', 'ETH') and quote assets (e.g., 'USDT').

    Notes:
    - Symbols must be Binance tickers (e.g., 'BTC', not CoinGecko IDs like 'bitcoin').
    - The 'currency' parameter is treated as the quote asset; 'usd' is mapped to 'USDT' for spot pairs.
    """

    BASE_URL = "https://api.binance.com"

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _quote_for_currency(self, currency: str) -> str:
        """
        Maps a generic currency string to a Binance quote asset.
        'usd' -> 'USDT' (most common spot quote), otherwise uppercase passthrough.
        """
        c = currency.upper()
        if c == "USD":
            return "USDT"
        return c

    def _pair(self, base_symbol: str, currency: str) -> str:
        """
        Builds a Binance trading pair, e.g., 'BTC' + 'USDT' -> 'BTCUSDT'.
        """
        return f"{base_symbol.upper()}{self._quote_for_currency(currency)}"

    async def get_price(self, symbol: str, currency: str = "usd") -> Optional[float]:
        """
        Fetches the current spot price using Binance ticker endpoint.

        Args:
            symbol: Binance base asset ticker (e.g., 'BTC', 'ETH').
            currency: Quote asset (e.g., 'usd' -> 'USDT', 'BUSD', 'USDT', etc.).

        Returns:
            The current price as a float, or None on error.
        """
        session = await self._get_session()
        pair = self._pair(symbol, currency)
        url = f"{self.BASE_URL}/api/v3/ticker/price"
        params = {"symbol": pair}
        try:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                price_str = data.get("price")
                if price_str is None:
                    logger.warning(f"No price found for {pair}")
                    return None
                return float(price_str)
        except aiohttp.ClientError as e:
            logger.error(f"Binance API error fetching price for {pair}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {pair}: {e}")
            return None

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int,
        currency: str = "usd",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches accurate OHLCV candlesticks from Binance.

        Args:
            symbol: Binance base asset ticker (e.g., 'BTC').
            interval: Binance interval (e.g., '1m', '5m', '1h', '4h', '1d').
            limit: Max number of klines to retrieve (1–1000 per Binance).
            currency: Quote asset; 'usd' maps to 'USDT'.

        Returns:
            A list of dicts: { timestamp, open, high, low, close, volume } or None on error.
        """
        session = await self._get_session()
        pair = self._pair(symbol, currency)
        url = f"{self.BASE_URL}/api/v3/klines"
        params = {"symbol": pair, "interval": interval, "limit": limit}
        try:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                klines: List[Dict[str, Any]] = []
                # Binance kline array format:
                # [0] openTime(ms), [1] open, [2] high, [3] low, [4] close, [5] volume,
                # [6] closeTime(ms), [7] quoteAssetVolume, [8] trades, [9] takerBuyBase,
                # [10] takerBuyQuote, [11] ignore
                for k in data:
                    klines.append({
                        "timestamp": int(k[0]),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                    })
                return klines
        except aiohttp.ClientError as e:
            logger.error(f"Binance API error fetching klines for {pair}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching klines for {pair}: {e}")
            return None

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("Binance client session closed.")