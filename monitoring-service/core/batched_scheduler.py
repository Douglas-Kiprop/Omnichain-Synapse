import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
from core.strategy_loader import StrategyLoader
from core.condition_evaluator import ConditionEvaluator, EvaluationContext
from core.logic_tree_evaluator import LogicTreeEvaluator
from core.data_prefetcher import DataPrefetcher
from models.strategy_models import Strategy, StrategyTriggerLog
from config import get_settings

logger = logging.getLogger(__name__)

class BatchedScheduler:
    def __init__(self, async_session_local) -> None:
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self.async_session_local = async_session_local
        settings = get_settings()
        self._prefetcher = DataPrefetcher(redis_url=settings.REDIS_URL)
        self.interval = settings.SCHEDULER_INTERVAL_SECONDS

    async def start(self) -> None:
        if self._task is None:
            self._running = True
            await self._prefetcher.connect()
            logger.info("BatchedScheduler started")
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
    
        await self._prefetcher.close()
        logger.info("BatchedScheduler stopped")

    async def _run(self) -> None:
        try:
            evaluator = ConditionEvaluator(self._prefetcher)
            logic = LogicTreeEvaluator(evaluator)
            while self._running:
                async with self.async_session_local() as session:
                    loader = StrategyLoader(session)
                    strategies: List[Strategy] = await loader.load_active_strategies()
                    logger.info(f"Scheduler cycle: loaded {len(strategies)} active strategies")
                    if not strategies:
                        logger.info("No active strategies found.")
                    else:
                        logger.info(f"Processing {len(strategies)} strategies...")
                    for s in strategies:
                        ctx = EvaluationContext(self._prefetcher)
                        res = await logic.evaluate(s, ctx)
                        s.last_run_at = datetime.utcnow()
                        logger.info(f"Strategy {s.id} evaluated: met={res.met}, details={res.details}")
                        if res.met:
                            s.trigger_count += 1
                            s.last_triggered_at = datetime.utcnow()
                            session.add(StrategyTriggerLog(strategy_id=s.id, snapshot=res.details, message=None))
                            logger.info(f"Trigger logged for strategy {s.id}")
                        session.add(s)
                    logger.info("Finished processing strategies for this cycle.")
                    await session.commit()
                    logger.info(f"Scheduler cycle committed for {len(strategies)} strategies")

                await asyncio.sleep(self.interval)
                logger.info("Scheduler resuming cycle.")
        except asyncio.CancelledError:
            logger.info("BatchedScheduler _run task cancelled.")
        except Exception as e:
            logger.exception(f"Unhandled exception in BatchedScheduler _run: {e}")
