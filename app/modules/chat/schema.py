from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    agent_type: Optional[str] = None
    confidence: Optional[float] = None
    sources: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SendMessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=5000)


class RenameSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    status: str
    agent_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: list[ChatMessage]


class ChatListResponse(BaseModel):
    sessions: list[ChatSessionResponse]
    total: int


class StreamingChunk(BaseModel):
    type: Literal["token", "metadata", "error", "done"]
    content: str = ""
    agent_type: Optional[str] = None
    session_id: Optional[str] = None
    sources: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
