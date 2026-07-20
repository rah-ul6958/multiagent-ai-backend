from datetime import datetime
from typing import Optional

from beanie import Document
from pydantic import Field


class AgentLog(Document):
    session_id: str
    message_id: str
    agent_type: str
    intent_detected: Optional[str] = None
    input_text: str
    output_text: str
    tools_used: list[str] = Field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0
    confidence: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    class Settings:
        name = "agent_logs"
        indexes = [
            "session_id",
            "agent_type",
            "success",
            "created_at",
        ]
