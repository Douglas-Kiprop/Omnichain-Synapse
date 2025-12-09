from typing import List
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models.strategy_models import Strategy, StrategyCondition, StrategyStatus

class StrategyLoader:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def load_active_strategies(self) -> List[Strategy]:
        """
        Loads all active strategies from the database that are due to run, eagerly loading their conditions.
        """
        result = await self.db_session.execute(
            select(Strategy)
            .where(Strategy.status == StrategyStatus.active)
            .options(selectinload(Strategy.conditions))
        )
        all_active_strategies = result.scalars().all()

        strategies_due_to_run = []
        now = datetime.now(timezone.utc)

        for strategy in all_active_strategies:
            if strategy.schedule == "event": # Event-driven strategies are not time-scheduled
                strategies_due_to_run.append(strategy)
                continue

            # Parse interval-based schedules (e.g., "1m", "5m", "1h")
            if strategy.schedule.endswith("m"):
                interval_minutes = int(strategy.schedule[:-1])
                interval = timedelta(minutes=interval_minutes)
            elif strategy.schedule.endswith("h"):
                interval_hours = int(strategy.schedule[:-1])
                interval = timedelta(hours=interval_hours)
            else:
                # Default to 1 minute if schedule is not recognized or is cron-like (not yet implemented)
                interval = timedelta(minutes=1)

            # Ensure last_run_at is timezone-aware if it exists
            last_run_at_aware = strategy.last_run_at.astimezone(timezone.utc) if strategy.last_run_at else None

            if last_run_at_aware is None or (now - last_run_at_aware) >= interval:
                strategies_due_to_run.append(strategy)

        return strategies_due_to_run

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
