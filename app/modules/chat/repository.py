from typing import Optional

from app.database.models.chat_session import ChatSession
from app.database.models.message import Message


class ChatRepository:
    async def create_session(
        self, user_id: str, title: str = "New Conversation"
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        return await session.insert()

    async def get_session(
        self, session_id: str
    ) -> Optional[ChatSession]:
        return await ChatSession.get(session_id)

    async def get_user_sessions(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ChatSession]:
        return (
            await ChatSession.find(
                ChatSession.user_id == user_id,
                ChatSession.status != "archived",
            )
            .sort("-updated_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def count_user_sessions(self, user_id: str) -> int:
        return await ChatSession.find(
            ChatSession.user_id == user_id,
            ChatSession.status != "archived",
        ).count()

    async def update_session(
        self, session: ChatSession
    ) -> ChatSession:
        from datetime import datetime

        session.updated_at = datetime.utcnow()
        return await session.save()

    async def close_session(self, session_id: str) -> bool:
        session = await ChatSession.get(session_id)
        if session:
            session.status = "closed"
            await self.update_session(session)
            return True
        return False

    async def create_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_type: str = None,
        confidence: float = None,
        sources: list = None,
        tokens_used: int = 0,
        latency_ms: float = 0.0,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            agent_type=agent_type,
            confidence=confidence,
            sources=sources or [],
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
        return await message.insert()

    async def get_session_messages(
        self,
        session_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Message]:
        return (
            await Message.find(
                Message.session_id == session_id
            )
            .sort("created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

    async def get_recent_messages(
        self, session_id: str, limit: int = 10
    ) -> list[Message]:
        messages = (
            await Message.find(
                Message.session_id == session_id
            )
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        return list(reversed(messages))

    async def count_session_messages(
        self, session_id: str
    ) -> int:
        return await Message.find(
            Message.session_id == session_id
        ).count()

    async def search_sessions(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
    ) -> list[ChatSession]:
        return (
            await ChatSession.find(
                ChatSession.user_id == user_id,
                ChatSession.title.contains(query, ignore_case=True),
            )
            .sort("-updated_at")
            .limit(limit)
            .to_list()
        )

    async def delete_session(self, session_id: str) -> bool:
        session = await ChatSession.get(session_id)
        if session:
            await Message.delete_many(
                Message.session_id == session_id
            )
            await session.delete()
            return True
        return False
