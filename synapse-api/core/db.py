from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# Database engine
engine = None
SessionLocal = None

class Base(DeclarativeBase):
    metadata = MetaData()


async def init_db():
    """Initialize database connection"""
    global engine, SessionLocal

    if not settings.POSTGRES_URL:
        raise ValueError("POSTGRES_URL environment variable is required")

    # Normalize scheme to asyncpg and strip quotes
    db_url = settings.POSTGRES_URL.strip().strip('"').strip("'")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Strip sslmode param from query
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
    parsed = urlparse(db_url)
    q = dict(parse_qsl(parsed.query))
    q.pop("sslmode", None)
    new_query = urlencode(q)
    db_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"ssl": True},  # Enable SSL for Supabase
    )

    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    logger.info("Database connection initialized")


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
    """Close database connection"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database connection closed")