from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from models.strategy_models import Strategy, StrategyCondition
from core.condition_evaluator import ConditionEvaluator, EvaluationContext, ConditionResult

@dataclass
class LogicResult:
    met: bool
    details: Dict[str, Any]

class LogicTreeEvaluator:
    def __init__(self, condition_evaluator: ConditionEvaluator):
        self.condition_evaluator = condition_evaluator

    async def evaluate(self, strategy: Strategy, ctx: EvaluationContext, currency: str = "usd") -> LogicResult:
        cond_map: Dict[str, StrategyCondition] = {str(c.id): c for c in strategy.conditions if c.enabled}
        cache: Dict[str, ConditionResult] = {}
        async def eval_node(node: Dict[str, Any]) -> bool:
            if "ref" in node:
                ref = str(node["ref"])
                if ref in cache:
                    return cache[ref].met
                cond = cond_map.get(ref)
                if not cond:
                    cache[ref] = ConditionResult(met=False, value=None, details={"missing_condition": True})
                    return False
                res = await self.condition_evaluator.evaluate(cond, ctx, currency)
                cache[ref] = res
                return res.met
            op = str(node.get("operator", "")).upper()
            children = node.get("conditions") or []
            if op == "AND":
                for child in children:
                    if not await eval_node(child):
                        return False
                return True
            if op == "OR":
                for child in children:
                    if await eval_node(child):
                        return True
                return False
            return False
        met = await eval_node(strategy.logic_tree or {})
        details = {
            "met": met,
            "evaluated": {k: {"met": v.met, "value": v.value, "details": v.details} for k, v in cache.items()}
        }
        return LogicResult(met=met, details=details)