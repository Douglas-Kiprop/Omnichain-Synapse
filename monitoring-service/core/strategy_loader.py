from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.strategy_models import Strategy, StrategyCondition, StrategyStatus

class StrategyLoader:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def load_active_strategies(self) -> List[Strategy]:
        """
        Loads all active strategies from the database, eagerly loading their conditions.
        """
        result = await self.db_session.execute(
            select(Strategy)
            .where(StrategyStatus.active == Strategy.status)
            .options(selectinload(Strategy.conditions))
        )
        return result.scalars().all()

    async def load_strategy_by_id(self, strategy_id: str) -> Strategy | None:
        """
        Loads a single strategy by its ID, eagerly loading its conditions.
        """
        result = await self.db_session.execute(
            select(Strategy)
            .where(Strategy.id == strategy_id)
            .options(selectinload(Strategy.conditions))
        )
        return result.scalars().first()
