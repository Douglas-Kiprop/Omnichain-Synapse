import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os

# Add the project root to sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.session import AsyncSessionLocal, engine, test_db_connection, close_db_connection
import aioredis
import os

# Load environment variables for testing
from dotenv import load_dotenv
load_dotenv()

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a session-scoped event loop for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_db_for_tests(event_loop):
    """
    Sets up the database connection for all tests in the session.
    """
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise ValueError("POSTGRES_URL environment variable not set for testing.")
    
    await test_db_connection(postgres_url)
    yield
    await close_db_connection()

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an independent, rollback-capable session for each test.
    """
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSessionLocal(bind=connection)

    try:
        yield session
    finally:
        await transaction.rollback()
        await connection.close()
        await session.close()

@pytest.fixture(scope="session")
async def setup_redis_for_tests(event_loop):
    """
    Sets up the Redis connection pool for all tests in the session.
    """
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise ValueError("REDIS_URL environment variable not set for testing.")
    
    pool = aioredis.ConnectionPool.from_url(redis_url)
    redis = aioredis.Redis(connection_pool=pool)
    
    # Clear Redis before tests to ensure a clean state
    await redis.flushdb()
    
    yield pool
    
    # Close Redis connection pool after tests
    await pool.disconnect()

@pytest.fixture
async def redis_client(setup_redis_for_tests) -> AsyncGenerator[aioredis.Redis, None]:
    """
    Provides a Redis client instance for each test.
    """
    pool = setup_redis_for_tests
    redis = aioredis.Redis(connection_pool=pool)
    yield redis
    # Clean up any keys set by the test
    await redis.flushdb()
    await redis.close()