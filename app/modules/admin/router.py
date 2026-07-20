import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.database.models.user import User
from app.modules.auth.dependencies import (
    get_current_admin_user,
    get_current_user,
)
from app.modules.admin.service import admin_service
from app.schemas.response import APIResponse

import logging
logger = logging.getLogger(__name__)


class SettingsUpdateRequest(BaseModel):
    provider: Optional[str] = None
    primary_model: Optional[str] = None
    fallback_model: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    top_k_retrieval: Optional[int] = None
    top_k_rerank: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    rate_limit_per_minute: Optional[int] = None
    log_level: Optional[str] = None
    debug: Optional[bool] = None

router = APIRouter()


class TraceBroadcaster:
    """In-memory SSE broadcaster for live orchestration traces."""

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, client_id: str) -> asyncio.Queue:
        async with self._lock:
            q: asyncio.Queue = asyncio.Queue()
            self._queues[client_id] = q
            return q

    async def unsubscribe(self, client_id: str):
        async with self._lock:
            self._queues.pop(client_id, None)

    async def broadcast(self, event: dict):
        async with self._lock:
            dead = []
            for cid, q in self._queues.items():
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead.append(cid)
            for cid in dead:
                self._queues.pop(cid, None)


trace_broadcaster = TraceBroadcaster()


@router.get(
    "/dashboard",
    response_model=APIResponse,
    summary="Get full dashboard with KPIs and charts",
)
async def get_dashboard(
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_dashboard()
    return APIResponse(
        message="Dashboard retrieved",
        data=result,
    )


@router.get(
    "/users",
    response_model=APIResponse,
    summary="List all users with filtering",
)
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(None),
    role: str = Query(None),
    status: str = Query(None),
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_users(
        skip, limit, search, role, status
    )
    return APIResponse(
        message="Users retrieved",
        data=result,
    )


@router.put(
    "/users/{user_id}",
    response_model=APIResponse,
    summary="Update user role or status",
)
async def update_user(
    user_id: str,
    role: str = Query(None),
    is_active: bool = Query(None),
    admin: User = Depends(get_current_admin_user),
):
    result = await admin_service.update_user(
        user_id, role, is_active
    )
    if not result:
        return APIResponse(
            success=False, message="User not found"
        )
    return APIResponse(
        message="User updated", data=result
    )


@router.delete(
    "/users/{user_id}",
    response_model=APIResponse,
    summary="Delete a user",
)
async def delete_user(
    user_id: str,
    admin: User = Depends(get_current_admin_user),
):
    success = await admin_service.delete_user(user_id)
    if not success:
        return APIResponse(
            success=False, message="User not found"
        )
    return APIResponse(message="User deleted")


@router.get(
    "/conversations",
    response_model=APIResponse,
    summary="List all conversations",
)
async def get_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Query(None),
    search: str = Query(None),
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_conversations(
        skip, limit, user_id, search=search
    )
    return APIResponse(
        message="Conversations retrieved",
        data=result,
    )


@router.get(
    "/conversations/{session_id}",
    response_model=APIResponse,
    summary="Get conversation detail with messages and logs",
)
async def get_conversation_detail(
    session_id: str,
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_conversation_detail(
        session_id
    )
    if not result:
        return APIResponse(
            success=False, message="Conversation not found"
        )
    return APIResponse(
        message="Conversation retrieved", data=result
    )


@router.delete(
    "/conversations/{session_id}",
    response_model=APIResponse,
    summary="Delete a conversation",
)
async def delete_conversation(
    session_id: str,
    admin: User = Depends(get_current_admin_user),
):
    success = await admin_service.delete_conversation(
        session_id
    )
    if not success:
        return APIResponse(
            success=False, message="Conversation not found"
        )
    return APIResponse(message="Conversation deleted")


@router.get(
    "/activity",
    response_model=APIResponse,
    summary="Get live activity panel data",
)
async def get_activity_panel(
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_activity_panel()
    return APIResponse(
        message="Activity panel retrieved",
        data=result,
    )


@router.get(
    "/agents",
    response_model=APIResponse,
    summary="Get AI agent monitoring data",
)
async def get_agent_monitoring(
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_agent_monitoring()
    return APIResponse(
        message="Agent monitoring retrieved",
        data=result,
    )


@router.get(
    "/vector-db",
    response_model=APIResponse,
    summary="Get vector database stats",
)
async def get_vector_db_stats(
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_vector_db_stats()
    return APIResponse(
        message="Vector DB stats retrieved",
        data=result,
    )


@router.post(
    "/vector-db/rebuild",
    response_model=APIResponse,
    summary="Rebuild FAISS index",
)
async def rebuild_index(
    admin: User = Depends(get_current_admin_user),
):
    try:
        from app.modules.knowledge_base.service import (
            KnowledgeBaseService,
        )

        kb = KnowledgeBaseService()
        result = await kb.reindex_documents(
            full_reindex=True
        )
        return APIResponse(
            message="Index rebuilt", data=result
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Rebuild failed: {str(e)}",
        )


@router.get(
    "/logs",
    response_model=APIResponse,
    summary="Get system agent logs",
)
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    result = await admin_service.get_logs(skip, limit)
    return APIResponse(
        message="Logs retrieved",
        data=result,
    )


@router.get(
    "/settings",
    response_model=APIResponse,
    summary="Get current system settings",
)
async def get_settings(
    user: User = Depends(get_current_user),
):
    result = admin_service.get_settings()
    return APIResponse(
        message="Settings retrieved",
        data=result,
    )


@router.put(
    "/settings",
    response_model=APIResponse,
    summary="Update system settings",
)
async def update_settings(
    data: SettingsUpdateRequest,
    user: User = Depends(get_current_user),
):
    result = admin_service.update_settings(data.model_dump(exclude_none=True))
    return APIResponse(
        message="Settings updated",
        data=result,
    )


@router.get(
    "/activity/stream",
    summary="SSE stream for live orchestration trace events",
)
async def activity_stream(
    request: Request,
    token: str = Query(None),
):
    import uuid
    from app.shared.security.jwt import decode_token
    from app.database.models.user import User as UserModel

    if not token:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'message': 'No token provided'})}\n\n"]),
            media_type="text/event-stream",
        )

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        user_id = payload.get("sub")
        user = await UserModel.get(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
    except Exception:
        logger.debug("SSE token validation failed", exc_info=True)
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'message': 'Invalid token'})}\n\n"]),
            media_type="text/event-stream",
        )

    client_id = str(uuid.uuid4())

    async def event_generator() -> AsyncGenerator[str, None]:
        queue = await trace_broadcaster.subscribe(client_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=30.0
                    )
                    yield f"data: {json.dumps(event, default=str)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await trace_broadcaster.unsubscribe(client_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
