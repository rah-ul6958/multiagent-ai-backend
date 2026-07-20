import logging
import time
from typing import AsyncGenerator

from app.core.exceptions import NotFoundError
from app.database.models.user import User
from app.modules.chat.repository import ChatRepository
from app.modules.chat.schema import (
    ChatHistoryResponse,
    ChatListResponse,
    ChatMessage,
    ChatSessionResponse,
    SendMessageRequest,
)

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.repository = ChatRepository()

    def _session_to_response(
        self, session, message_count: int = 0
    ) -> ChatSessionResponse:
        return ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            status=session.status,
            agent_type=session.agent_type,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
        )

    async def send_message(
        self,
        user: User,
        data: SendMessageRequest,
    ) -> AsyncGenerator[dict, None]:
        if data.session_id:
            session = await self.repository.get_session(
                data.session_id
            )
            if not session or session.user_id != str(user.id):
                session = await self.repository.create_session(
                    str(user.id),
                    title=data.message[:50] + "...",
                )
        else:
            session = await self.repository.create_session(
                str(user.id),
                title=data.message[:50] + "...",
            )

        user_msg = await self.repository.create_message(
            session_id=str(session.id),
            role="user",
            content=data.message,
        )

        start_time = time.time()

        yield {
            "type": "metadata",
            "session_id": str(session.id),
            "agent_type": "intent_detection",
        }

        try:
            from app.ai.graph.orchestrator import (
                OrchestratorGraph,
            )
            from app.modules.admin.router import trace_broadcaster

            async def trace_broadcast(event):
                await trace_broadcaster.broadcast({
                    **event,
                    "session_id": str(session.id),
                })

            orchestrator = OrchestratorGraph(trace_callback=trace_broadcast)

            recent_messages = (
                await self.repository.get_recent_messages(
                    str(session.id), limit=10
                )
            )

            conversation_history = [
                {"role": m.role, "content": m.content}
                for m in recent_messages
            ]

            full_response = ""
            agent_type = "general"
            sources = []

            async for chunk in orchestrator.process(
                message=data.message,
                conversation_history=conversation_history,
                session_id=str(session.id),
                user_id=str(user.id),
                message_id=str(user_msg.id),
            ):
                if chunk.get("type") == "token":
                    full_response += chunk.get("content", "")
                    yield chunk
                elif chunk.get("type") == "metadata":
                    agent_type = chunk.get(
                        "agent_type", agent_type
                    )
                    sources = chunk.get("sources", sources)
                    yield chunk

        except Exception as e:
            logger.error(f"AI processing error: {e}")
            full_response = (
                "I apologize, but I encountered an error "
                "processing your request. Please try again."
            )
            agent_type = "error"
            yield {
                "type": "error",
                "content": full_response,
            }

        latency_ms = (time.time() - start_time) * 1000

        await self.repository.create_message(
            session_id=str(session.id),
            role="assistant",
            content=full_response,
            agent_type=agent_type,
            sources=sources,
            latency_ms=latency_ms,
        )

        session.title = (
            data.message[:50] + "..."
            if len(data.message) > 50
            else data.message
        )
        session.agent_type = agent_type
        await self.repository.update_session(session)

        try:
            from app.modules.admin.router import trace_broadcaster
            await trace_broadcaster.broadcast({
                "type": "done",
                "session_id": str(session.id),
                "agent_type": agent_type,
                "latency_ms": latency_ms,
            })
        except Exception:
            logger.debug("Trace broadcast failed", exc_info=True)

        yield {
            "type": "done",
            "session_id": str(session.id),
            "agent_type": agent_type,
            "latency_ms": latency_ms,
        }

    async def get_chat_history(
        self,
        user: User,
        session_id: str,
    ) -> ChatHistoryResponse:
        session = await self.repository.get_session(session_id)
        if not session or session.user_id != str(user.id):
            raise NotFoundError("Session not found")

        messages = await self.repository.get_session_messages(
            session_id
        )

        message_count = await self.repository.count_session_messages(
            session_id
        )

        return ChatHistoryResponse(
            session=self._session_to_response(
                session, message_count
            ),
            messages=[
                ChatMessage(
                    role=m.role,
                    content=m.content,
                    agent_type=m.agent_type,
                    confidence=m.confidence,
                    sources=m.sources,
                    created_at=m.created_at,
                )
                for m in messages
            ],
        )

    async def list_sessions(
        self,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> ChatListResponse:
        sessions = await self.repository.get_user_sessions(
            str(user.id), skip, limit
        )

        total = await self.repository.count_user_sessions(
            str(user.id)
        )

        session_responses = []
        for session in sessions:
            msg_count = (
                await self.repository.count_session_messages(
                    str(session.id)
                )
            )
            session_responses.append(
                self._session_to_response(session, msg_count)
            )

        return ChatListResponse(
            sessions=session_responses, total=total
        )

    async def search_sessions(
        self,
        user: User,
        query: str,
    ) -> list[ChatSessionResponse]:
        sessions = await self.repository.search_sessions(
            str(user.id), query
        )
        return [
            self._session_to_response(s) for s in sessions
        ]

    async def delete_session(
        self,
        user: User,
        session_id: str,
    ) -> bool:
        session = await self.repository.get_session(session_id)
        if not session or session.user_id != str(user.id):
            raise NotFoundError("Session not found")

        return await self.repository.delete_session(session_id)

    async def rename_session(
        self,
        user: User,
        session_id: str,
        title: str,
    ) -> dict:
        session = await self.repository.get_session(session_id)
        if not session or session.user_id != str(user.id):
            raise NotFoundError("Session not found")

        session.title = title
        await self.repository.update_session(session)
        return {
            "id": str(session.id),
            "title": session.title,
            "status": session.status,
            "agent_type": session.agent_type,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    async def toggle_pin_session(
        self,
        user: User,
        session_id: str,
    ) -> dict:
        session = await self.repository.get_session(session_id)
        if not session or session.user_id != str(user.id):
            raise NotFoundError("Session not found")

        session.is_pinned = not session.is_pinned
        await self.repository.update_session(session)
        return {
            "id": str(session.id),
            "title": session.title,
            "is_pinned": session.is_pinned,
        }
