from datetime import datetime
from typing import Literal, Optional

from beanie import Document
from pydantic import Field


class Feedback(Document):
    session_id: str
    message_id: str
    user_id: str
    rating: Literal["positive", "negative"]
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "feedback"
        indexes = [
            "session_id",
            "user_id",
            "rating",
            "created_at",
        ]
