from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text


engine = None
AsyncSessionLocal = None

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def test_db_connection(postgres_url: str) -> None:
    global engine, AsyncSessionLocal
    try:
        url = postgres_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        


        engine = create_async_engine(url, pool_pre_ping=True)
        AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as e:
        raise RuntimeError(f"Postgres connection failed: {str(e)}") from e

async def close_db_connection() -> None:
    global engine
    if engine:
        await engine.dispose()