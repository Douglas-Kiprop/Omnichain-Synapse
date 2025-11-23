from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from core.config import settings
import logging
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

logger = logging.getLogger(__name__)

engine = None
AsyncSessionLocal = None


class Base(DeclarativeBase):
    metadata = MetaData()


async def init_db():
    global engine, AsyncSessionLocal

    if not settings.POSTGRES_URL:
        raise ValueError("POSTGRES_URL is required")

    raw_url = settings.POSTGRES_URL.strip().strip('"').strip("'")

    # Force psycopg-binary driver
    if raw_url.startswith("postgres://"):
        db_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif raw_url.startswith("postgresql://") and "+psycopg" not in raw_url:
        db_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    else:
        db_url = raw_url

    # Clean sslmode
    parsed = urlparse(db_url)
    q = dict(parse_qsl(parsed.query))
    q.pop("sslmode", None)
    db_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(q), parsed.fragment))

    engine = create_async_engine(
        db_url,
        echo=False,
        future=True,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info("SUPABASE CONNECTED — psycopg-binary — IT WORKS ON WINDOWS")


async def get_db() -> AsyncSession:
    if AsyncSessionLocal is None:
        raise RuntimeError("DB not initialized")
    async with AsyncSessionLocal() as session:
        yield session


async def close_db():
    global engine
    if engine:
        await engine.dispose()
        logger.info("DB closed")