import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db
from core.security import get_current_user
from core.errors import NotFoundError
from auth.models import UserProfile
from .service import StrategyService
from .models import StrategyCreateSchema, StrategyReadSchema, StrategyStatus

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/strategies", response_model=StrategyReadSchema)
async def create_strategy(
    payload: StrategyCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    logger.info(f"Received strategy creation request for user {current_user.id}: {payload.json()}")
    svc = StrategyService(db)
    return await svc.create_strategy(current_user, payload)


@router.get("/strategies", response_model=List[StrategyReadSchema])
async def list_strategies(
    status: Optional[StrategyStatus] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    svc = StrategyService(db)
    return await svc.list_strategies(current_user, status.value if status else None)


@router.get("/strategies/{strategy_id}", response_model=StrategyReadSchema)
async def get_strategy(
    strategy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    svc = StrategyService(db)
    try:
        return await svc.get_strategy(current_user, strategy_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Strategy not found")


@router.put("/strategies/{strategy_id}", response_model=StrategyReadSchema)
async def update_strategy(
    strategy_id: UUID,
    payload: StrategyCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    svc = StrategyService(db)
    try:
        return await svc.update_strategy(current_user, strategy_id, payload)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Strategy not found")


@router.delete("/strategies/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    svc = StrategyService(db)
    await svc.delete_strategy(current_user, strategy_id)
    return None