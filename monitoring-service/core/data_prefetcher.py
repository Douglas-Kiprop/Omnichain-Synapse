import asyncio
from typing import Dict, List, Optional, Any
import aioredis
import json
import logging
from clients.async_binance import AsyncBinanceClient
from clients.async_coingecko import AsyncCoinGeckoClient

logger = logging.getLogger(__name__)

class DataPrefetcher:
    def __init__(self, redis_url: Optional[str] = None) -> None:
        self._redis_url = redis_url
        self._pool: Optional[aioredis.ConnectionPool] = None
        self._binance: Optional[AsyncBinanceClient] = None
        self._coingecko: Optional[AsyncCoinGeckoClient] = None

    async def connect(self) -> None:
        if self._redis_url and self._pool is None:
            self._pool = aioredis.ConnectionPool.from_url(self._redis_url)
        if self._binance is None:
            self._binance = AsyncBinanceClient()
        if self._coingecko is None:
            self._coingecko = AsyncCoinGeckoClient()

    async def close(self) -> None:
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        if self._binance:
            await self._binance.close()
            self._binance = None
        if self._coingecko:
            await self._coingecko.close()
            self._coingecko = None

    async def get_prices(self, assets: List[str], currency: str = "usd", ttl_seconds: int = 30) -> Dict[str, Optional[float]]:
        result: Dict[str, Optional[float]] = {}
        redis: Optional[aioredis.Redis] = None
        if self._pool:
            redis = aioredis.Redis(connection_pool=self._pool)
        for a in assets:
            key = f"prices:{a}"
            val: Optional[float] = None
            if redis:
                logger.debug(f"Checking cache for {key}")
                raw = await redis.get(key)
                if raw is not None:
                    try:
                        val = float(raw)
                        logger.debug(f"Cache hit for {key}: {val}")
                    except Exception:
                        logger.warning(f"Cached value for {key} is not a float")
                        val = None
            if val is None:
                fetched = await self.fetch_price(a, currency)
                if fetched is not None:
                    val = fetched
                    if redis:
                        await redis.setex(key, ttl_seconds, str(fetched))
                        logger.debug(f"Caching price for {key} with TTL {ttl_seconds}")
                else:
                    logger.debug(f"No price fetched for {a}")
            result[a] = val
        return result

    async def set_price(self, asset: str, price: float, ttl_seconds: int = 30) -> None:
        if self._pool:
            async with aioredis.Redis(connection_pool=self._pool) as redis:
                await redis.setex(f"prices:{asset}", ttl_seconds, str(price))

    async def fetch_price(self, asset: str, currency: str = "usd") -> Optional[float]:
        val: Optional[float] = None
        if self._binance:
            val = await self._binance.get_price(asset, currency)
        if val is None and self._coingecko:
            val = await self._coingecko.get_price(asset, currency)
        return val

    async def get_klines(self, symbol: str, interval: str, limit: int, currency: str = "usd", ttl_seconds: int = 60) -> Optional[List[Dict[str, Any]]]:
        key = f"klines:{symbol}:{interval}:{limit}:{currency}"
        logger.debug(f"Attempting to get klines for {key}")
        redis: Optional[aioredis.Redis] = None
        if self._pool:
            redis = aioredis.Redis(connection_pool=self._pool)

        if redis:
            cached_klines_raw = await redis.get(key)
            if cached_klines_raw:
                try:
                    logger.debug(f"Klines found in cache for {key}")
                    return json.loads(cached_klines_raw)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode cached klines for {key}. Attempting to refetch.")

        klines: Optional[List[Dict[str, Any]]] = None
        if self._binance:
            logger.debug(f"Fetching klines from Binance for {key}")
            klines = await self._binance.get_klines(symbol, interval, limit, currency)
            if klines:
                logger.debug(f"Successfully fetched {len(klines)} klines from Binance for {symbol}.")
            else:
                logger.debug(f"No klines fetched from Binance for {symbol}.")
        
        if klines is None and self._coingecko:
            logger.debug(f"Binance returned no klines or is unavailable. Attempting CoinGecko for {key}")
            # CoinGecko provides price and volume, not full OHLCV. Adjust expectations.
            klines = await self._coingecko.get_klines(symbol, interval, limit, currency)
            if klines:
                logger.info(f"Fetched {len(klines)} klines from CoinGecko for {symbol} (price/volume only).")
            else:
                logger.debug(f"No klines fetched from CoinGecko for {symbol}.")

        if klines and redis:
            logger.debug(f"Caching klines for {key} with TTL {ttl_seconds}s.")
            await redis.setex(key, ttl_seconds, json.dumps(klines))
        
        return klines