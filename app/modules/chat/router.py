import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.chat.schema import SendMessageRequest, RenameSessionRequest
from app.modules.chat.service import ChatService
from app.schemas.response import APIResponse

router = APIRouter()
service = ChatService()


@router.post(
    "/send",
    summary="Send a chat message with streaming response",
)
async def send_message(
    data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
):
    async def event_stream():
        async for chunk in service.send_message(
            current_user, data
        ):
            yield f"data: {json.dumps(chunk, default=str)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/sessions",
    response_model=APIResponse,
    summary="List chat sessions",
)
async def list_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    result = await service.list_sessions(
        current_user, skip, limit
    )
    sessions_payload = []
    for session in getattr(result, "sessions", []) or []:
        sessions_payload.append(
            session.model_dump()
            if hasattr(session, "model_dump")
            else session
        )
    return APIResponse(
        message="Sessions retrieved",
        data={
            "sessions": sessions_payload,
            "total": getattr(result, "total", len(sessions_payload)),
        },
    )


@router.get(
    "/sessions/{session_id}",
    response_model=APIResponse,
    summary="Get chat history",
)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    result = await service.get_chat_history(
        current_user, session_id
    )
    payload = (
        result.model_dump()
        if hasattr(result, "model_dump")
        else result
    )
    return APIResponse(
        message="Chat history retrieved",
        data=payload,
    )


@router.get(
    "/search",
    response_model=APIResponse,
    summary="Search chat sessions",
)
async def search_sessions(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
):
    results = await service.search_sessions(current_user, q)
    return APIResponse(
        message="Search results",
        data={
            "sessions": [s.model_dump() for s in results]
        },
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=APIResponse,
    summary="Delete a chat session",
)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    await service.delete_session(current_user, session_id)
    return APIResponse(message="Session deleted")


@router.put(
    "/sessions/{session_id}/rename",
    response_model=APIResponse,
    summary="Rename a chat session",
)
async def rename_session(
    session_id: str,
    data: RenameSessionRequest,
    current_user: User = Depends(get_current_user),
):
    result = await service.rename_session(
        current_user, session_id, data.title
    )
    return APIResponse(
        message="Session renamed",
        data=result,
    )


@router.put(
    "/sessions/{session_id}/pin",
    response_model=APIResponse,
    summary="Toggle pin on a chat session",
)
async def toggle_pin_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    result = await service.toggle_pin_session(
        current_user, session_id
    )
    return APIResponse(
        message="Session pin toggled",
        data=result,
    )
