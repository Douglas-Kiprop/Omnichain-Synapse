import aioredis
from typing import Optional

redis_pool: Optional[aioredis.ConnectionPool] = None

async def test_redis_connection(redis_url: str) -> None:
    global redis_pool
    try:
        redis_pool = aioredis.ConnectionPool.from_url(redis_url)
        async with aioredis.Redis(connection_pool=redis_pool) as redis:
            await redis.ping()
    except Exception as e:
        raise RuntimeError(f"Redis connection failed: {str(e)}") from e

async def close_redis_connection() -> None:
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()