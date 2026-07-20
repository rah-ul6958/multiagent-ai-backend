from typing import Optional

from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    total_sessions: int
    total_messages: int
    total_documents: int
    total_tickets: int
    open_tickets: int
    recent_activity: list[dict]


class UserManagementResponse(BaseModel):
    users: list[dict]
    total: int


class SystemHealthResponse(BaseModel):
    mongodb_status: str
    ai_service_status: str
    vector_store_status: str
    uptime: float
    version: str
