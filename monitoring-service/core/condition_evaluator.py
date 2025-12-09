from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime
from models.strategy_models import StrategyCondition
from core.data_prefetcher import DataPrefetcher

@dataclass
class ConditionResult:
    met: bool
    value: Optional[float] = None
    details: Dict[str, Any] = None

class EvaluationContext:
    def __init__(self, prefetcher: DataPrefetcher, now: Optional[datetime] = None, prior_state: Optional[Dict[str, Any]] = None):
        self.prefetcher = prefetcher
        self.now = now or datetime.utcnow()
        self.prior_state = prior_state or {}
        self.price_cache: Dict[str, float] = {}
        self.klines_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.indicator_cache: Dict[str, Any] = {}

class Indicator:
    @staticmethod
    def sma(values: List[float], period: int) -> Optional[float]:
        if len(values) < period or period <= 0:
            return None
        return sum(values[-period:]) / period
    @staticmethod
    def ema(values: List[float], period: int) -> Optional[float]:
        if len(values) < period or period <= 0:
            return None
        k = 2 / (period + 1)
        ema = values[0]
        for v in values[1:]:
            ema = v * k + ema * (1 - k)
        return ema
    @staticmethod
    def rsi(values: List[float], period: int) -> Optional[float]:
        if len(values) < period + 1 or period <= 0:
            return None
        gains = 0.0
        losses = 0.0
        for i in range(-period, 0):
            delta = values[i] - values[i - 1]
            if delta >= 0:
                gains += delta
            else:
                losses -= delta
        if losses == 0:
            return 100.0
        rs = gains / losses
        return 100.0 - (100.0 / (1.0 + rs))
    @staticmethod
    def stddev(values: List[float], period: int) -> Optional[float]:
        if len(values) < period or period <= 0:
            return None
        window = values[-period:]
        m = sum(window) / period
        var = sum((v - m) ** 2 for v in window) / period
        return var ** 0.5
    @staticmethod
    def bollinger(values: List[float], period: int, mult: float) -> Optional[Tuple[float, float, float]]:
        sma = Indicator.sma(values, period)
        if sma is None:
            return None
        sd = Indicator.stddev(values, period)
        if sd is None:
            return None
        upper = sma + mult * sd
        lower = sma - mult * sd
        return sma, upper, lower
    @staticmethod
    def macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Tuple[float, float, float]]:
        if len(values) < slow + signal or fast <= 0 or slow <= 0 or signal <= 0:
            return None
        macd_line_series: List[float] = []
        for i in range(slow, len(values) + 1):
            slice_vals = values[:i]
            ema_fast = Indicator.ema(slice_vals, fast)
            ema_slow = Indicator.ema(slice_vals, slow)
            if ema_fast is None or ema_slow is None:
                continue
            macd_line_series.append(ema_fast - ema_slow)
        if len(macd_line_series) < signal:
            return None
        signal_line = Indicator.ema(macd_line_series, signal)
        if signal_line is None:
            return None
        macd_line = macd_line_series[-1]
        hist = macd_line - signal_line
        return macd_line, signal_line, hist

class ConditionEvaluator:
    def __init__(self, prefetcher: DataPrefetcher):
        self.prefetcher = prefetcher

    async def _ensure_price(self, ctx: EvaluationContext, asset: str, currency: str) -> Optional[float]:
        key = f"{asset}:{currency}"
        if key in ctx.price_cache:
            return ctx.price_cache[key]
        await self.prefetcher.connect()
        prices = await self.prefetcher.get_prices([asset], currency)
        val = prices.get(asset)
        if isinstance(val, (int, float)):
            ctx.price_cache[key] = float(val)
            return float(val)
        return None

    async def _ensure_klines(self, ctx: EvaluationContext, asset: str, interval: str, limit: int, currency: str) -> Optional[List[Dict[str, Any]]]:
        key = f"{asset}:{interval}:{limit}:{currency}"
        if key in ctx.klines_cache:
            return ctx.klines_cache[key]
        await self.prefetcher.connect()
        kl = await self.prefetcher.get_klines(asset, interval, limit, currency)
        if kl is not None:
            ctx.klines_cache[key] = kl
            return kl
        return None

    def _close_series(self, klines: List[Dict[str, Any]]) -> List[float]:
        return [float(k["close"]) for k in klines if "close" in k]

    def _volume_series(self, klines: List[Dict[str, Any]]) -> List[float]:
        vals: List[float] = []
        for k in klines:
            v = k.get("volume")
            if v is None:
                v = k.get("vol") or k.get("quote_volume") or k.get("quoteVolume")
            if v is None:
                continue
            try:
                vals.append(float(v))
            except Exception:
                continue
        return vals

    def _compare(self, lhs: Optional[float], op: str, rhs: float) -> bool:
        if lhs is None:
            return False
        if op == "gt":
            return lhs > rhs
        if op == "ge":
            return lhs >= rhs
        if op == "lt":
            return lhs < rhs
        if op == "le":
            return lhs <= rhs
        if op == "eq":
            return lhs == rhs
        return False

    def _cross(self, prev: Optional[float], curr: Optional[float], direction: str, threshold: float) -> bool:
        if prev is None or curr is None:
            return False
        if direction == "cross_above":
            return prev <= threshold and curr > threshold
        if direction == "cross_below":
            return prev >= threshold and curr < threshold
        return False

    async def evaluate(self, condition: StrategyCondition, ctx: EvaluationContext, currency: str = "usd") -> ConditionResult:
        if not condition.enabled:
            return ConditionResult(met=False, value=None, details={"disabled": True})
        t = (condition.type or "").strip().lower()
        if t == "price_alert":
            payload = condition.payload or {}
            asset = str(payload.get("asset", "")).upper()
            direction = str(payload.get("direction", "")).lower()
            target = payload.get("target_price")
            if not asset or direction not in {"above", "below"} or not isinstance(target, (int, float)):
                return ConditionResult(met=False, value=None, details={"invalid": True})
            price = await self._ensure_price(ctx, asset, currency)
            if price is None:
                return ConditionResult(met=False, value=None, details={"source_unavailable": True})
            met = price > float(target) if direction == "above" else price < float(target)
            return ConditionResult(met=met, value=price, details={"asset": asset, "direction": direction, "target": float(target)})
        if t == "technical_indicator":
            payload = condition.payload or {}
            indicator = str(payload.get("indicator", "")).lower()
            params = payload.get("params") or {}
            op = str(payload.get("operator", "")).lower()
            rhs = payload.get("value")
            asset = str(payload.get("asset", "")).upper()
            interval = str(payload.get("timeframe", "1h")).lower()
            if not asset or indicator == "" or not isinstance(rhs, (int, float)):
                return ConditionResult(met=False, value=None, details={"invalid": True})

            if indicator in {"price", "price_change"}:
                price = await self._ensure_price(ctx, asset, currency)
                if price is None:
                    return ConditionResult(met=False, value=None, details={"source_unavailable": True})
                if op in {"gt", "ge", "lt", "le", "eq"}:
                    met = self._compare(price, op, float(rhs))
                elif op in {"cross_above", "cross_below"}:
                    prev_price: Optional[float] = None
                    met = self._cross(prev_price, price, op, float(rhs))
                else:
                    return ConditionResult(met=False, value=None, details={"unknown_operator": op})
                return ConditionResult(met=bool(met), value=price, details={"indicator": "price", "operator": op, "threshold": float(rhs), "asset": asset})

            needed_limit = 0
            if indicator == "rsi":
                period = int(params.get("period", 14))
                needed_limit = period + 1
            elif indicator in {"sma", "ema"}:
                period = int(params.get("period", 14))
                needed_limit = max(period + 1 if op.startswith("cross_") else period, 2)
            elif indicator == "macd":
                fast = int(params.get("fast", 12))
                slow = int(params.get("slow", 26))
                signal = int(params.get("signal", 9))
                needed_limit = slow + signal
            elif indicator == "bollinger":
                period = int(params.get("period", 20))
                needed_limit = period
            elif indicator == "volume":
                needed_limit = 2 if op.startswith("cross_") else 1
            else:
                return ConditionResult(met=False, value=None, details={"unknown_indicator": indicator})
            kl = await self._ensure_klines(ctx, asset, interval, needed_limit, currency)
            if not kl or len(kl) < needed_limit:
                return ConditionResult(met=False, value=None, details={"insufficient_data": True})
            closes = self._close_series(kl)
            val: Optional[float] = None
            prev_val: Optional[float] = None
            if indicator == "rsi":
                period = int(params.get("period", 14))
                val = Indicator.rsi(closes, period)
                if op.startswith("cross_") and len(closes) >= period + 2:
                    pv = Indicator.rsi(closes[:-1], period)
                    prev_val = pv
            elif indicator == "sma":
                period = int(params.get("period", 20))
                val = Indicator.sma(closes, period)
                if op.startswith("cross_"):
                    prev_val = Indicator.sma(closes[:-1], period)
            elif indicator == "ema":
                period = int(params.get("period", 20))
                val = Indicator.ema(closes, period)
                if op.startswith("cross_"):
                    prev_val = Indicator.ema(closes[:-1], period)
            elif indicator == "macd":
                fast = int(params.get("fast", 12))
                slow = int(params.get("slow", 26))
                signal = int(params.get("signal", 9))
                macd_tuple = Indicator.macd(closes, fast, slow, signal)
                if macd_tuple is None:
                    return ConditionResult(met=False, value=None, details={"insufficient_data": True})
                val = macd_tuple[0]
                if op.startswith("cross_"):
                    macd_prev = Indicator.macd(closes[:-1], fast, slow, signal)
                    prev_val = macd_prev[0] if macd_prev else None
            elif indicator == "bollinger":
                period = int(params.get("period", 20))
                mult = float(params.get("mult", 2.0))
                bb = Indicator.bollinger(closes, period, mult)
                if bb is None:
                    return ConditionResult(met=False, value=None, details={"insufficient_data": True})
                band = str(params.get("band", "upper")).lower()
                if band == "upper":
                    val = bb[1]
                elif band == "lower":
                    val = bb[2]
                else:
                    val = bb[0]
                if op.startswith("cross_"):
                    bb_prev = Indicator.bollinger(closes[:-1], period, mult)
                    if bb_prev:
                        if band == "upper":
                            prev_val = bb_prev[1]
                        elif band == "lower":
                            prev_val = bb_prev[2]
                        else:
                            prev_val = bb_prev[0]
            elif indicator == "volume":
                vols = self._volume_series(kl)
                val = vols[-1] if vols else None
                if op.startswith("cross_"):
                    prev_val = vols[-2] if len(vols) >= 2 else None
            if op in {"gt", "ge", "lt", "le", "eq"}:
                met = self._compare(val, op, float(rhs))
            elif op in {"cross_above", "cross_below"}:
                met = self._cross(prev_val, val, op, float(rhs))
            else:
                return ConditionResult(met=False, value=None, details={"unknown_operator": op})
            return ConditionResult(met=bool(met), value=val, details={"indicator": indicator, "operator": op, "threshold": float(rhs), "asset": asset, "interval": interval})
        return ConditionResult(met=False, value=None, details={"unknown_type": t})