from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text


engine = None
AsyncSessionLocal = None

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to yield an async database session.
    """
    async with AsyncSessionLocal() as session:
        yield session

async def test_db_connection(postgres_url: str) -> None:
    """
    Initializes the SQLAlchemy async engine and tests the connection.
    
    The engine configuration includes fixes for the 'prepared statement does not exist' error.
    """
    global engine, AsyncSessionLocal
    try:
        url = postgres_url
        
        # Standardize URL for use with psycopg (async driver)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        # --- FIXES FOR InvalidSqlStatementName ARE APPLIED HERE ---
        # 1. pool_recycle: Ensures connections are recycled periodically.
        # 2. connect_args: Specifically disables prepared statements 
        #    to prevent PgBouncer/connection reset issues.
        engine = create_async_engine(
            url, 
            pool_pre_ping=True, 
            pool_recycle=1800,  # Recycle connections every 30 minutes (1800 seconds)
            connect_args={
                "prepare_threshold": None  # Disables prepared statements (solves psycopg.errors.InvalidSqlStatementName)
            }
        )
        # --- END OF FIXES ---
        
        AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
        
        # Test connection
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            
    except Exception as e:
        raise RuntimeError(f"Postgres connection failed: {str(e)}") from e

async def close_db_connection() -> None:
    """
    Disposes of the database engine and closes all pooled connections.
    """
    global engine
    if engine:
        await engine.dispose()