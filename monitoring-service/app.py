from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from api.strategies import router as strategies_router
from core.batched_scheduler import BatchedScheduler
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategies_router, prefix="/internal")


@app.get("/health")
async def health():
    return {"status": "ok"}


from cache.redis_client import test_redis_connection
from db.session import test_db_connection

@app.on_event("startup")
async def on_startup():
    settings = get_settings()
    if not settings.REDIS_URL:
        raise ValueError("Missing REDIS_URL in .env")
    try:
        await test_redis_connection(settings.REDIS_URL)
    except Exception as e:
        logging.error(f"Redis connection failed: {e}")
    if settings.POSTGRES_URL:
        try:
            await test_db_connection(settings.POSTGRES_URL)
            from db.session import AsyncSessionLocal
            if settings.ENABLE_SCHEDULER:
                app.state.scheduler = BatchedScheduler(AsyncSessionLocal)
                await app.state.scheduler.start()
        except Exception as e:
            logging.error(f"Postgres connection failed: {e}")
    else:
        logging.warning("Skipping Postgres check: POSTGRES_URL not configured")


from cache.redis_client import close_redis_connection
from db.session import close_db_connection

@app.on_event("shutdown")
async def on_shutdown():
    if hasattr(app.state, "scheduler") and app.state.scheduler:
        await app.state.scheduler.stop()
    await close_redis_connection()
    await close_db_connection()
