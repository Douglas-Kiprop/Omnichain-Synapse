from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseClient(ABC):
    """
    Abstract base class for all external data provider clients.
    Defines a common interface for fetching market data such as prices and klines.
    """

    @abstractmethod
    async def get_price(self, symbol: str, currency: str = "usd") -> Optional[float]:
        """
        Fetches the current price of a given symbol in a specified currency.

        Args:
            symbol: The symbol of the asset (e.g., "bitcoin", "ethereum").
            currency: The currency to get the price in (e.g., "usd", "eur").

        Returns:
            The current price as a float, or None if not found.
        """
        pass

    @abstractmethod
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int,
        currency: str = "usd",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetches historical kline (candlestick) data for a given symbol.

        Args:
            symbol: The symbol of the asset.
            interval: The time interval for klines (e.g., "1m", "1h", "1d").
            limit: The maximum number of klines to retrieve.
            currency: The currency relevant for the kline data (if applicable).

        Returns:
            A list of dictionaries, each representing a kline, or None if not found.
            Each dictionary should contain at least 'timestamp', 'open', 'high', 'low', 'close', 'volume'.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """
        Closes any open connections or sessions for the client.
        This should be called during application shutdown.
        """
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
