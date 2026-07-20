from datetime import datetime
from typing import Literal, Optional

from beanie import Document
from pydantic import Field


class Ticket(Document):
    user_id: str
    session_id: Optional[str] = None
    subject: str
    description: str
    status: Literal["open", "in_progress", "resolved", "closed"] = "open"
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    category: str = "general"
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "tickets"
        indexes = [
            "user_id",
            "status",
            "priority",
            "assigned_to",
            "created_at",
        ]
