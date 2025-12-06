import aiohttp
from typing import Any, Dict, List, Optional
from .base import BaseClient
import logging

logger = logging.getLogger(__name__)

class AsyncCoinGeckoClient(BaseClient):
    """
    Asynchronous client for interacting with the CoinGecko API.
    Implements the BaseClient interface for fetching cryptocurrency prices and klines.
    """
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Ensures a single aiohttp ClientSession is used."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_price(self, symbol: str, currency: str = "usd") -> Optional[float]:
        """
        Fetches the current price of a given symbol from CoinGecko.

        Args:
            symbol: The CoinGecko ID of the asset (e.g., "bitcoin", "ethereum").
            currency: The currency to get the price in (e.g., "usd", "eur").

        Returns:
            The current price as a float, or None if not found or an error occurs.
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}/simple/price"
        params = {"ids": symbol, "vs_currencies": currency}
        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors
                data = await response.json()
                price = data.get(symbol, {}).get(currency)
                if price is None:
                    logger.warning(f"Price not found for {symbol} in {currency}")
                return price
        except aiohttp.ClientError as e:
            logger.error(f"CoinGecko API error fetching price for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    async def get_klines(
        self,
        symbol: str,
        interval: str, # CoinGecko uses 'daily' for 1d, 'hourly' for 1h, etc.
        limit: int, # CoinGecko's 'days' parameter is not a direct limit, but a range.
        currency: str = "usd",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches historical kline (candlestick) data for a given symbol from CoinGecko.
        Note: CoinGecko's API for klines (market_charts) uses 'days' as a range, not a direct limit.
        This implementation will fetch data for a number of days that roughly covers the 'limit'
        based on the interval. For simplicity, we'll use 'days=1' for '1h' and '1d' intervals
        to get recent data, and then process it. A more robust solution would map intervals
        to appropriate 'days' values.

        Args:
            symbol: The CoinGecko ID of the asset.
            interval: The time interval for klines (e.g., "1h", "1d").
                      CoinGecko's API expects 'hourly' for 1h, 'daily' for 1d.
                      This client will attempt to map common intervals.
            limit: The maximum number of klines to retrieve.
            currency: The currency for the market data (e.g., "usd").

        Returns:
            A list of dictionaries, each representing a kline, or None if not found.
            Each dictionary will contain 'timestamp', 'price', 'volume'.
        """
        session = await self._get_session()
        url = f"{self.BASE_URL}/coins/{symbol}/market_chart"

        # CoinGecko's market_chart API uses 'vs_currency' and 'days' (range), not 'interval' and 'limit' directly.
        # We need to map our generic interval/limit to CoinGecko's parameters.
        # For simplicity, let's assume '1h' and '1d' intervals for now and fetch data for a few days.
        # A more sophisticated mapping would be needed for other intervals.
        coingecko_interval_map = {
            "1h": "hourly",
            "1d": "daily",
            # Add more mappings as needed
        }
        coingecko_days_map = {
            "1h": 1, # Fetch data for the last day for hourly
            "1d": 7, # Fetch data for the last 7 days for daily
        }

        coingecko_interval = coingecko_interval_map.get(interval)
        days_to_fetch = coingecko_days_map.get(interval, 1) # Default to 1 day if interval not mapped

        if not coingecko_interval:
            logger.error(f"Unsupported interval for CoinGecko: {interval}")
            return None

        params = {
            "vs_currency": currency,
            "days": days_to_fetch,
            "interval": coingecko_interval # This parameter is sometimes ignored or inferred by 'days'
        }

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                klines = []
                # CoinGecko returns prices, market_caps, and total_volumes separately.
                # We need to combine them to form klines (candlesticks).
                # This is a simplification; a true kline requires OHLCV data, which CoinGecko's
                # market_chart endpoint doesn't directly provide in OHLCV format.
                # It provides price at a given timestamp.
                # For a proper kline, we'd need an endpoint that provides OHLCV or
                # to derive it from minute-level data, which is beyond this initial scope.
                # For now, we'll just return price data as a list of dicts with timestamp and price.
                # This will need to be refined if true OHLCV klines are required.

                prices_data = data.get("prices", [])
                volumes_data = data.get("total_volumes", [])

                # Create a mapping from timestamp to volume for easier lookup
                volume_map = {p[0]: p[1] for p in volumes_data}

                for price_entry in prices_data:
                    timestamp_ms = price_entry[0]
                    price = price_entry[1]
                    volume = volume_map.get(timestamp_ms, 0) # Get corresponding volume

                    # CoinGecko's market_chart provides a single price point per timestamp.
                    # To simulate OHLCV, we'll use the price as open, high, low, close for simplicity.
                    # This is a placeholder and should be replaced with actual OHLCV data if available
                    # from another CoinGecko endpoint or a different provider.
                    klines.append({
                        "timestamp": timestamp_ms,
                        "price": price,
                        "volume": volume,
                    })
                
                # Limit the number of klines returned to the requested limit
                return klines[-limit:] if len(klines) > limit else klines

        except aiohttp.ClientError as e:
            logger.error(f"CoinGecko API error fetching klines for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

    async def close(self) -> None:
        """Closes the aiohttp client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("CoinGecko client session closed.")
