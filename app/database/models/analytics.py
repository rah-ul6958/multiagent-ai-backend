from datetime import datetime

from beanie import Document
from pydantic import Field


class DailyAnalytics(Document):
    date: datetime
    total_conversations: int = 0
    total_messages: int = 0
    unique_users: int = 0
    avg_response_time_ms: float = 0.0
    avg_confidence: float = 0.0
    positive_feedback: int = 0
    negative_feedback: int = 0
    tickets_created: int = 0
    tickets_resolved: int = 0
    agent_distribution: dict = Field(default_factory=dict)
    intent_distribution: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "analytics"
        indexes = [
            "date",
        ]
