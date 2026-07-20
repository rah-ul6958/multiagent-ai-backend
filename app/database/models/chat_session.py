from datetime import datetime
from typing import Literal, Optional

from beanie import Document
from pydantic import Field


class ChatSession(Document):
    user_id: str
    title: str = "New Conversation"
    status: Literal["active", "closed", "archived"] = "active"
    agent_type: Optional[str] = None
    is_pinned: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    class Settings:
        name = "chat_sessions"
        indexes = [
            "user_id",
            "status",
            "created_at",
        ]
