from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolCallRequest(BaseModel):
    session_id: str = Field(default="demo-session", min_length=1, max_length=120)
    tool: Literal["shell", "filesystem.list", "filesystem.read", "filesystem.write", "web.search"]
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    event_id: int
    verdict: Literal["allow", "deny", "escalate", "confirm"]
    reason: str
    screening_source: str
    executed: bool
    result: Any | None = None
    forensic_analysis: str | None = None
    latency_ms: float
