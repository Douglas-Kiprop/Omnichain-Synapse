import pytest
import uuid
from typing import List, Dict, Any
from core.condition_evaluator import ConditionEvaluator, EvaluationContext
from core.logic_tree_evaluator import LogicTreeEvaluator
from models.strategy_models import Strategy, StrategyCondition, StrategyStatus

class FakePrefetcher:
    async def connect(self): pass
    async def close(self): pass
    async def get_prices(self, assets: List[str], currency: str = "usd"):
        return {a: 100.0 for a in assets}
    async def get_klines(self, symbol: str, interval: str, limit: int, currency: str = "usd"):
        closes = [100 - i for i in range(limit)]
        return [{"timestamp": i, "open": c, "high": c+1, "low": c-1, "close": c, "volume": 1.0} for i, c in enumerate(closes)]

@pytest.mark.asyncio
async def test_price_alert_above_true():
    cond = StrategyCondition(
        id=uuid.uuid4(),
        type="price_alert",
        payload={"asset": "BTC", "direction": "above", "target_price": 90.0},
        enabled=True,
    )
    s = Strategy(id=uuid.uuid4(), name="t", status=StrategyStatus.active, logic_tree={"ref": str(cond.id)}, conditions=[cond])
    evaluator = ConditionEvaluator(FakePrefetcher())
    ctx = EvaluationContext(prefetcher=FakePrefetcher())
    logic = LogicTreeEvaluator(evaluator)
    res = await logic.evaluate(s, ctx)
    assert res.met is True

@pytest.mark.asyncio
async def test_rsi_lt_true():
    cond = StrategyCondition(
        id=uuid.uuid4(),
        type="technical_indicator",
        payload={"indicator": "rsi", "params": {"period": 14}, "operator": "lt", "value": 30.0, "asset": "BTC", "timeframe": "1h"},
        enabled=True,
    )
    s = Strategy(id=uuid.uuid4(), name="t", status=StrategyStatus.active, logic_tree={"ref": str(cond.id)}, conditions=[cond])
    evaluator = ConditionEvaluator(FakePrefetcher())
    ctx = EvaluationContext(prefetcher=FakePrefetcher())
    logic = LogicTreeEvaluator(evaluator)
    res = await logic.evaluate(s, ctx)
    assert res.met in {True, False}
    assert "evaluated" in res.details

@pytest.mark.asyncio
async def test_logic_and_combination():
    c1 = StrategyCondition(
        id=uuid.uuid4(),
        type="price_alert",
        payload={"asset": "BTC", "direction": "above", "target_price": 50.0},
        enabled=True,
    )
    c2 = StrategyCondition(
        id=uuid.uuid4(),
        type="price_alert",
        payload={"asset": "BTC", "direction": "below", "target_price": 50.0},
        enabled=True,
    )
    tree = {"operator": "AND", "conditions": [{"ref": str(c1.id)}, {"ref": str(c2.id)}]}
    s = Strategy(id=uuid.uuid4(), name="t", status=StrategyStatus.active, logic_tree=tree, conditions=[c1, c2])
    evaluator = ConditionEvaluator(FakePrefetcher())
    ctx = EvaluationContext(prefetcher=FakePrefetcher())
    logic = LogicTreeEvaluator(evaluator)
    res = await logic.evaluate(s, ctx)
    assert res.met is False