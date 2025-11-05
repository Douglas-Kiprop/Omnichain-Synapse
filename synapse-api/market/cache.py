from cachetools import TTLCache
import asyncio
from typing import Any, Optional

# Create a TTL (Time To Live) cache for market data
# Maxsize is the maximum number of items the cache can hold
# TTL is the time-to-live in seconds for each cached item
market_cache = TTLCache(maxsize=100, ttl=300)  # Cache for 5 minutes (300 seconds)

# Create a separate cache for volume analysis data
volume_cache = TTLCache(maxsize=50, ttl=300)  # Cache for 5 minutes (300 seconds)

async def get_cached_data(key: str, cache: TTLCache) -> Optional[Any]:
    """Retrieves data from the cache if it exists."""
    return cache.get(key)

async def set_cached_data(key: str, data: Any, cache: TTLCache) -> None:
    """Stores data in the cache with the specified key."""
    cache[key] = data

async def clear_cache(cache: TTLCache) -> None:
    """Clears all items from the specified cache."""
    cache.clear()

def generate_cache_key(*args) -> str:
    """Generates a cache key from the provided arguments."""
    return ":".join(str(arg) for arg in args)