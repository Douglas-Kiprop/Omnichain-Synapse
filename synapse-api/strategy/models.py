# models.py
from __future__ import annotations
from datetime import datetime
import enum
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Boolean,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from pydantic import BaseModel, Field, validator

from core.db import Base  # your SQLAlchemy declarative base


# -------------------------
# SQLAlchemy models (DB)
# -------------------------

class StrategyStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    archived = "archived"
    error = "error"


class LogicOperator(str, enum.Enum):
    AND = "AND"
    OR = "OR"


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)

    # The canonical normalized condition records are stored in strategy_conditions
    # 'logic_tree' refers to condition/group structure using refs to condition ids (see Pydantic schema)
    logic_tree = Column(JSONB, nullable=False, default={})  # {"operator":"AND", "conditions":[{"ref":"c1"}, {"operator":"OR","conditions":[{"ref":"c2"},{"ref":"c3"}]}]}

    # optional materialized list of condition ids (helpful for quick queries)
    condition_ids = Column(JSONB, nullable=False, default=list)

    # schedule: cron-like or simple interval (1m,5m,1h) or "event"
    schedule = Column(String, nullable=False, default="1m")

    # assets explicitly referenced by strategy (for data prefetching)
    assets = Column(JSONB, nullable=False, default=list)

    # notification preferences follow a validated JSON schema (see Pydantic below)
    notification_preferences = Column(JSONB, nullable=False, default={})

    # engine metadata: required data sources, last run times, derived info
    required_data = Column(JSONB, nullable=False, default={})

    # stats
    last_run_at = Column(DateTime, nullable=True)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, nullable=False, default=0)

    status = Column(SQLEnum(StrategyStatus), nullable=False, default=StrategyStatus.active)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    conditions = relationship("StrategyCondition", cascade="all, delete-orphan", back_populates="strategy")
    trigger_logs = relationship("StrategyTriggerLog", cascade="all, delete-orphan", back_populates="strategy")


Index("ix_strategies_user_status", Strategy.user_id, Strategy.status)


class StrategyCondition(Base):
    __tablename__ = "strategy_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    # normalized type of condition, e.g., price_alert, technical_indicator, wallet_inflow, volume_spike, custom_script
    type = Column(String, nullable=False, index=True)

    # Canonical payload for the condition. Example shapes:
    # - price_alert: {"asset":"BTC","direction":"below","target_price":60000}
    # - technical_indicator: {"indicator":"rsi","params":{"period":14},"operator":"lt","value":30,"asset":"BTC","timeframe":"1h"}
    payload = Column(JSONB, nullable=False, default={})

    # optional human-friendly label
    label = Column(String, nullable=True)

    # whether this condition is enabled individually
    enabled = Column(Boolean, nullable=False, default=True)

    # created/updated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    strategy = relationship("Strategy", back_populates="conditions")


class StrategyTriggerLog(Base):
    __tablename__ = "strategy_trigger_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)

    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    # store snapshot of data that caused the trigger for audit (prices, candles, indicator values, group evaluation result)
    snapshot = Column(JSONB, nullable=False, default={})

    # optional text message sent to user
    message = Column(String, nullable=True)

    strategy = relationship("Strategy", back_populates="trigger_logs")


# -------------------------
# Pydantic schemas (API / validation)
# -------------------------

# Notification schemas
class NotificationChannel(BaseModel):
    enabled: bool = True
    # Only one of the following is expected depending on channel
    telegram_chat_id: Optional[str] = None
    email: Optional[str] = None
    webhook_url: Optional[str] = None
    # provider specific config (e.g., telegram bot id, slack webhook settings)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class NotificationEvents(BaseModel):
    trigger: bool = True
    reset: bool = False
    error: bool = True
    cooldown_end: bool = False


class NotificationCooldown(BaseModel):
    enabled: bool = False
    duration: Optional[str] = None  # ISO 8601 or "1h", "10m"


class NotificationPreferences(BaseModel):
    channels: Dict[str, NotificationChannel] = Field(default_factory=dict)
    alert_on: NotificationEvents = NotificationEvents()
    cooldown: NotificationCooldown = NotificationCooldown()


# Condition payload examples are in "payload" field of StrategyCondition DB model.
class ConditionPayload(BaseModel):
    # type-specific validation should be applied at service layer
    indicator: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    operator: Optional[str] = None
    value: Optional[float] = None
    asset: Optional[str] = None
    direction: Optional[str] = None
    threshold: Optional[float] = None


class ConditionCreate(BaseModel):
    id: Optional[uuid.UUID] = None
    type: str
    payload: Dict[str, Any]
    label: Optional[str] = None
    enabled: bool = True


class ConditionRead(ConditionCreate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# Logic tree node
class LogicNode(BaseModel):
    operator: Optional[LogicOperator] = None  # present for group nodes
    # either conditions (refs) or nested groups
    conditions: Optional[List[Dict[str, Any]]] = None
    # example: {"ref": "<condition_id>"} or nested node
    # validators will ensure structure correctness


class StrategyCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    schedule: str = "1m"
    assets: List[str] = Field(default_factory=list)
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences)
    # flattened canonical conditions
    conditions: List[ConditionCreate] = Field(default_factory=list)
    # logic tree uses refs to condition ids (or temporary client refs)
    logic_tree: Dict[str, Any] = Field(..., description="Logic tree referencing conditions via {ref: '<id>'} or nested groups")
    status: Optional[StrategyStatus] = StrategyStatus.active

    @validator("logic_tree")
    def validate_logic_tree(cls, v, values):
        # basic structural validation (deferred heavy validation to service)
        if not isinstance(v, dict) or "operator" not in v:
            raise ValueError("logic_tree must be a dict with an 'operator' field (AND/OR)")
        if v.get("operator") not in {op.value for op in LogicOperator}:
            raise ValueError("logic_tree.operator must be 'AND' or 'OR'")
        return v


class StrategyReadSchema(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    schedule: str
    assets: List[str]
    notification_preferences: NotificationPreferences
    conditions: List[ConditionRead]
    logic_tree: Dict[str, Any]
    required_data: Dict[str, Any]
    status: StrategyStatus
    last_run_at: Optional[datetime]
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
