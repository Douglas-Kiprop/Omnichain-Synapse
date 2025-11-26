from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from core.errors import NotFoundError
from auth.models import UserProfile
from .models import (
    Strategy,
    StrategyCondition,
    StrategyCreateSchema,
    StrategyReadSchema,
    ConditionRead,
    StrategyStatus,
)

class StrategyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_strategy(self, current_user: UserProfile, payload: StrategyCreateSchema) -> StrategyReadSchema:
        # Assign stable UUIDs to conditions (use provided id or generate)
        cond_id_map: Dict[str, UUID] = {}
        normalized_conditions = []
        for c in payload.conditions:
            cid = c.id or uuid4()
            cond_id_map[str(c.id) if c.id else str(cid)] = cid
            normalized_conditions.append(
                StrategyCondition(
                    id=cid,
                    type=c.type,
                    payload=c.payload,
                    label=c.label,
                    enabled=c.enabled,
                )
            )

        # Rewrite logic_tree refs to actual UUID strings
        rewritten_tree = self._rewrite_logic_refs(payload.logic_tree, cond_id_map)

        # Create strategy
        strategy = Strategy(
            user_id=current_user.id,
            name=payload.name,
            description=payload.description,
            logic_tree=rewritten_tree,
            condition_ids=[str(cid) for cid in cond_id_map.values()],
            schedule=payload.schedule,
            assets=payload.assets,
            notification_preferences=payload.notification_preferences.dict() if hasattr(payload.notification_preferences, "dict") else payload.notification_preferences,
            required_data={},  # can be derived by evaluator later
            status=payload.status or StrategyStatus.active,
        )
        self.db.add(strategy)
        await self.db.flush()  # get strategy.id before creating condition rows

        # Attach conditions to this strategy
        for sc in normalized_conditions:
            sc.strategy_id = strategy.id
            self.db.add(sc)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            from core.errors import ConflictError
            raise ConflictError("Strategy creation failed due to integrity constraints")

        await self.db.refresh(strategy)
        # Load conditions back for response
        conds = await self._fetch_conditions(strategy.id)
        return self._to_read_schema(strategy, conds)

    async def list_strategies(self, current_user: UserProfile, status: Optional[str] = None) -> List[StrategyReadSchema]:
        stmt = select(Strategy).where(Strategy.user_id == current_user.id)
        if status:
            stmt = stmt.where(Strategy.status == StrategyStatus(status))
        res = await self.db.execute(stmt.order_by(Strategy.created_at.desc()))
        items = res.scalars().all()

        result: List[StrategyReadSchema] = []
        for s in items:
            conds = await self._fetch_conditions(s.id)
            result.append(self._to_read_schema(s, conds))
        return result

    async def get_strategy(self, current_user: UserProfile, strategy_id: UUID) -> StrategyReadSchema:
        res = await self.db.execute(
            select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
        )
        strategy = res.scalar_one_or_none()
        if not strategy:
            raise NotFoundError("Strategy not found")

        conds = await self._fetch_conditions(strategy.id)
        return self._to_read_schema(strategy, conds)

    async def update_strategy(self, current_user: UserProfile, strategy_id: UUID, payload: StrategyCreateSchema) -> StrategyReadSchema:
        # Ensure strategy exists
        res = await self.db.execute(
            select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
        )
        strategy = res.scalar_one_or_none()
        if not strategy:
            raise NotFoundError("Strategy not found")

        # Delete existing conditions (full replace semantics)
        await self.db.execute(delete(StrategyCondition).where(StrategyCondition.strategy_id == strategy_id))

        # Recreate conditions with new IDs (or provided)
        cond_id_map: Dict[str, UUID] = {}
        for c in payload.conditions:
            cid = c.id or uuid4()
            cond_id_map[str(c.id) if c.id else str(cid)] = cid
            self.db.add(
                StrategyCondition(
                    id=cid,
                    strategy_id=strategy_id,
                    type=c.type,
                    payload=c.payload,
                    label=c.label,
                    enabled=c.enabled,
                )
            )

        rewritten_tree = self._rewrite_logic_refs(payload.logic_tree, cond_id_map)

        try:
            await self.db.execute(
                update(Strategy)
                .where(Strategy.id == strategy_id)
                .values(
                    name=payload.name,
                    description=payload.description,
                    logic_tree=rewritten_tree,
                    condition_ids=[str(cid) for cid in cond_id_map.values()],
                    schedule=payload.schedule,
                    assets=payload.assets,
                    notification_preferences=payload.notification_preferences.dict() if hasattr(payload.notification_preferences, "dict") else payload.notification_preferences,
                    status=payload.status or StrategyStatus.active,
                )
            )
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            from core.errors import ConflictError
            raise ConflictError("Strategy update failed due to integrity constraints")

        # Reload and return
        res = await self.db.execute(
            select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
        )
        updated = res.scalar_one_or_none()
        conds = await self._fetch_conditions(strategy_id)
        return self._to_read_schema(updated, conds)

    async def delete_strategy(self, current_user: UserProfile, strategy_id: UUID) -> None:
        # StrategyConditions have cascade delete; ensure ownership
        res = await self.db.execute(
            select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
        )
        strategy = res.scalar_one_or_none()
        if not strategy:
            raise NotFoundError("Strategy not found")

        await self.db.execute(delete(Strategy).where(Strategy.id == strategy_id))
        await self.db.commit()

    async def _fetch_conditions(self, strategy_id: UUID) -> List[ConditionRead]:
        res = await self.db.execute(
            select(StrategyCondition).where(StrategyCondition.strategy_id == strategy_id)
        )
        items = res.scalars().all()
        out: List[ConditionRead] = []
        for i in items:
            out.append(
                ConditionRead(
                    id=i.id,
                    type=i.type,
                    payload=i.payload,
                    label=i.label,
                    enabled=i.enabled,
                    created_at=i.created_at,
                    updated_at=i.updated_at,
                )
            )
        return out

    def _to_read_schema(self, s: Strategy, conds: List[ConditionRead]) -> StrategyReadSchema:
        return StrategyReadSchema(
            id=s.id,
            user_id=s.user_id,
            name=s.name,
            description=s.description,
            schedule=s.schedule,
            assets=s.assets or [],
            notification_preferences=s.notification_preferences or {},
            conditions=conds,
            logic_tree=s.logic_tree or {},
            required_data=s.required_data or {},
            status=s.status,
            last_run_at=s.last_run_at,
            last_triggered_at=s.last_triggered_at,
            trigger_count=s.trigger_count or 0,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )

    def _rewrite_logic_refs(self, node: Dict[str, Any], id_map: Dict[str, UUID]) -> Dict[str, Any]:
        # Recursively walk logic_tree; rewrite {"ref": "<client-id>"} to {"ref": "<uuid>"}
        def rewrite(n: Any) -> Any:
            if isinstance(n, dict):
                if "ref" in n and isinstance(n["ref"], str):
                    ref = n["ref"]
                    if ref in id_map:
                        return {"ref": str(id_map[ref])}
                    # leave as-is if unknown; service-level deep validation can enforce later
                # recurse for nested group nodes
                out = {}
                for k, v in n.items():
                    out[k] = rewrite(v)
                return out
            elif isinstance(n, list):
                return [rewrite(x) for x in n]
            else:
                return n

        return rewrite(node)