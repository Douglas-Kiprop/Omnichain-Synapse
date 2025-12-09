from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.session import get_db
from models.strategy_models import Strategy, StrategyTriggerLog
from config import Settings
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
import uuid
from core.strategy_loader import StrategyLoader
from models.strategy_models import StrategyStatus
from core.data_prefetcher import DataPrefetcher
from core.condition_evaluator import ConditionEvaluator, EvaluationContext
from core.logic_tree_evaluator import LogicTreeEvaluator
import aioredis

router = APIRouter()

# Instantiate settings globally or use a dependency if settings are dynamic
settings = Settings()

async def require_api_key(x_monitoring_key: str = Header(None, alias="X-Monitoring-Key")) -> None:
    if not settings.MONITORING_API_KEY or x_monitoring_key != settings.MONITORING_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/strategies")
async def list_strategies(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """
    Retrieves a list of active strategies from the database.
    This endpoint demonstrates fetching data using the SQLAlchemy async session.
    """
    strategy_loader = StrategyLoader(db)
    strategies = await strategy_loader.load_active_strategies()
    return [
        {
            "id": s.id,
            "name": s.name,
            "status": s.status.value,
            "schedule": s.schedule,
            "last_triggered_at": s.last_triggered_at,
            "trigger_count": s.trigger_count,
        }
        for s in strategies
    ]


class StrategyTriggerLogCreate(BaseModel):
    strategy_id: uuid.UUID
    name: str
    status: Literal["TRIGGERED", "HELD", "FAILED"]
    snapshot: Dict[str, Any] = Field(default_factory=dict)
    message: Optional[str] = None


@router.post("/trigger_log", status_code=status.HTTP_201_CREATED)
async def create_trigger_log(
    log_data: StrategyTriggerLogCreate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """
    Creates a new strategy trigger log entry in the database.
    """
    strategy_loader = StrategyLoader(db)
    strategy = await strategy_loader.load_strategy_by_id(log_data.strategy_id)
    if strategy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    # Update strategy's last_triggered_at and increment trigger_count
    strategy.last_triggered_at = func.now()
    strategy.trigger_count += 1
    db.add(strategy) # Mark the strategy as modified

    # Add name and status to snapshot
    log_data.snapshot["strategy_name"] = log_data.name
    log_data.snapshot["trigger_status"] = log_data.status

    new_log = StrategyTriggerLog(
        strategy_id=log_data.strategy_id,
        snapshot=log_data.snapshot,
        message=log_data.message,
    )
    db.add(new_log)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create trigger log: {e}")
    await db.refresh(new_log)
    return {"message": "Trigger log created successfully", "log_id": str(new_log.id)}

@router.post("/reload_strategies")
@router.post("/reload-strategies")
async def reload_strategies(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    strategy_loader = StrategyLoader(db)
    strategies = await strategy_loader.load_active_strategies()
    total = len(strategies)
    return {"reloaded": total}

@router.get("/simulate/{strategy_id}")
async def simulate_strategy(
    strategy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    strategy_loader = StrategyLoader(db)
    strategy = await strategy_loader.load_strategy_by_id(str(strategy_id))
    if strategy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    snapshot = {
        "strategy_id": str(strategy.id),
        "name": strategy.name,
        "schedule": strategy.schedule,
        "evaluated": True,
        "conditions_met": True,
    }
    return {"snapshot": snapshot}

@router.get("/metrics")
async def metrics(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    strategy_loader = StrategyLoader(db)
    active_strategies = await strategy_loader.load_active_strategies()
    s_count = len(active_strategies)
    t_count = (await db.execute(select(func.count(StrategyTriggerLog.id)))).scalar_one()
    return {
        "active_strategies": s_count,
        "total_trigger_logs": t_count,
    }

@router.get("/trigger_logs")
async def get_trigger_logs(
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """
    Retrieves a list of all strategy trigger logs from the database.
    """
    result = await db.execute(select(StrategyTriggerLog))
    trigger_logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "strategy_id": log.strategy_id,
            "timestamp": log.triggered_at,
            "snapshot": log.snapshot,
            "message": log.message,
        }
        for log in trigger_logs
    ]


class StrategyStatusUpdate(BaseModel):
    status: StrategyStatus

@router.put("/strategies/{strategy_id}/status", status_code=status.HTTP_200_OK)
async def update_strategy_status(
    strategy_id: uuid.UUID,
    status_update: StrategyStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    """
    Updates the status of a specific strategy.
    """
    strategy_loader = StrategyLoader(db)
    strategy = await strategy_loader.load_strategy_by_id(str(strategy_id))

    if strategy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")

    strategy.status = status_update.status
    db.add(strategy)
    try:
        await db.commit()
        await db.refresh(strategy)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to update strategy status: {e}")

    return {"message": f"Strategy {strategy_id} status updated to {status_update.status.value}", "new_status": strategy.status.value}

@router.post("/evaluate/{strategy_id}")
async def evaluate_strategy(
    strategy_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_api_key),
):
    loader = StrategyLoader(db)
    strategy = await loader.load_strategy_by_id(str(strategy_id))
    if strategy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    pref = DataPrefetcher(redis_url=settings.REDIS_URL)
    await pref.connect()
    try:
        evaluator = ConditionEvaluator(pref)
        logic = LogicTreeEvaluator(evaluator)
        ctx = EvaluationContext(pref)
        res = await logic.evaluate(strategy, ctx)
        return {"met": res.met, "details": res.details}
    finally:
        await pref.close()

@router.get("/cache/get")
async def cache_get(
    key: str,
    _: None = Depends(require_api_key),
):
    if not settings.REDIS_URL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="REDIS_URL not configured")
    pool = aioredis.ConnectionPool.from_url(settings.REDIS_URL)
    async with aioredis.Redis(connection_pool=pool) as redis:
        raw = await redis.get(key)
        val = raw.decode() if isinstance(raw, (bytes, bytearray)) else raw
        return {"key": key, "value": val}