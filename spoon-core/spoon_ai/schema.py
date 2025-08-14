from enum import Enum
from typing import Any, List, Literal, Optional, Union
from datetime import datetime
import uuid

from pydantic import BaseModel, Field


class Function(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Function

class AgentState(str, Enum):
    """
    The state of the agent.
    """
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"

class ToolChoice(str, Enum):
    """Tool choice options"""
    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


class Role(str, Enum):
    """Message role options"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

ROLE_VALUES = tuple(role.value for role in Role)
ROLE_TYPE = Literal[ROLE_VALUES]  # type: ignore


class Message(BaseModel):
    """Represents a chat message in the conversation"""

    role: ROLE_TYPE = Field(...) # type: ignore
    content: Optional[str] = Field(default=None)
    tool_calls: Optional[List[ToolCall]] = Field(default=None)
    name: Optional[str] = Field(default=None)
    tool_call_id: Optional[str] = Field(default=None)


TOOL_CHOICE_VALUES = tuple(choice.value for choice in ToolChoice)
TOOL_CHOICE_TYPE = Literal[TOOL_CHOICE_VALUES] # type: ignore

class LLMResponse(BaseModel):
    content: str
    tool_calls: List[Any] = Field(default_factory=list)
    finish_reason: Optional[str] = Field(default=None)
    native_finish_reason: Optional[str] = Field(default=None)


class Strategy(BaseModel):
    """
    Represents a data analysis strategy with conditions and actions
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Unique name for the strategy")
    description: Optional[str] = Field(default=None)
    conditions: List[str] = Field(
        ...,
        description="List of conditions that trigger this strategy"
    )
    actions: List[str] = Field(
        ...,
        description="Actions to execute when conditions are met"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)
    owner_id: Optional[str] = Field(default=None)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
