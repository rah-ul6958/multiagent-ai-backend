import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ConversationMemory:
    def __init__(self):
        self.max_history = 20

    async def get_history(
        self, session_id: str
    ) -> list[dict[str, str]]:
        try:
            from app.database.models.message import Message

            messages = (
                await Message.find(
                    Message.session_id == session_id
                )
                .sort("-created_at")
                .limit(self.max_history)
                .to_list()
            )

            history = []
            for msg in reversed(messages):
                history.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                    }
                )

            return history

        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        try:
            from app.database.models.message import Message

            message = Message(
                session_id=session_id,
                role=role,
                content=content,
            )
            await message.insert()

        except Exception as e:
            logger.error(f"Error adding message: {e}")

    async def summarize(
        self, messages: list[dict[str, str]]
    ) -> str:
        if not messages:
            return ""

        if len(messages) <= 3:
            return "\n".join(
                f"{m['role']}: {m['content']}"
                for m in messages
            )

        try:
            from app.ai.llm.service import llm_service
            from langchain_core.messages import HumanMessage

            conversation_text = "\n".join(
                f"{m['role']}: {m['content']}"
                for m in messages
            )

            prompt = f"""Summarize the following conversation concisely, capturing key points and user needs:

{conversation_text}

Provide a brief summary (2-3 sentences):"""

            result = await llm_service.invoke_with_metadata(
                [HumanMessage(content=prompt)],
                temperature=0.3,
                max_tokens=256,
            )
            return result.get("content", "")

        except Exception as e:
            logger.error(f"Error summarizing: {e}")
            recent = messages[-3:]
            return "\n".join(
                f"{m['role']}: {m['content']}"
                for m in recent
            )

    async def get_context_window(
        self,
        session_id: str,
        max_tokens: int = 4000,
    ) -> list[dict[str, str]]:
        history = await self.get_history(session_id)

        result = []
        current_tokens = 0

        for msg in reversed(history):
            estimated_tokens = len(msg["content"]) // 4
            if current_tokens + estimated_tokens > max_tokens:
                break
            result.insert(0, msg)
            current_tokens += estimated_tokens

        return result
