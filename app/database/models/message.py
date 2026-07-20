from datetime import datetime
from typing import Literal, Optional

from beanie import Document
from pydantic import Field


class Message(Document):
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    agent_type: Optional[str] = None
    confidence: Optional[float] = None
    sources: list[dict] = Field(default_factory=list)
    tokens_used: int = 0
    latency_ms: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    class Settings:
        name = "messages"
        indexes = [
            "session_id",
            "role",
            "created_at",
        ]
