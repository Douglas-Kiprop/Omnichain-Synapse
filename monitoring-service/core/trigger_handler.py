from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from models.strategy_models import Strategy, StrategyTriggerLog

class TriggerHandler:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def insert_trigger(self, strategy: Strategy, snapshot: Dict[str, Any], message: Optional[str]) -> StrategyTriggerLog:
        strategy.last_triggered_at = func.now()
        strategy.trigger_count += 1
        self.db.add(strategy)
        log = StrategyTriggerLog(strategy_id=strategy.id, snapshot=snapshot, message=message)
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log