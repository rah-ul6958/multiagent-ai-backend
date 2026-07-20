from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_conversations: int
    total_messages: int
    total_users: int
    avg_response_time_ms: float
    avg_confidence: float
    positive_feedback_pct: float
    conversations_today: int
    messages_today: int


class AgentAnalytics(BaseModel):
    agent_type: str
    total_invocations: int
    avg_confidence: float
    avg_latency_ms: float
    success_rate: float


class IntentAnalytics(BaseModel):
    intent: str
    count: int
    percentage: float


class TimeSeriesData(BaseModel):
    date: str
    value: float


class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview
    agent_breakdown: list[AgentAnalytics]
    intent_breakdown: list[IntentAnalytics]
    conversation_trend: list[TimeSeriesData]
    response_time_trend: list[TimeSeriesData]
