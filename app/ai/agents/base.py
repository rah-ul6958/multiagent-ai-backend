import time
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from app.ai.llm.service import llm_service
from app.core.config import settings


class BaseAgent(ABC):
    """Base class for all AI agents with LLM integration."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.llm = llm_service

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def get_user_prompt(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> str:
        pass

    async def process(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        start_time = time.time()

        system_prompt = self.get_system_prompt()
        user_prompt = self.get_user_prompt(
            message, context
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        result = await self.llm.invoke_with_metadata(
            messages
        )

        latency_ms = (time.time() - start_time) * 1000

        return {
            "response": result["content"],
            "agent": self.name,
            "provider": result.get("provider", "unknown"),
            "model": result.get("model", "unknown"),
            "latency_ms": latency_ms,
            "usage": result.get("usage", {}),
        }

    def _format_conversation_history(
        self, history: list[dict]
    ) -> str:
        if not history:
            return "No previous conversation."
        lines = []
        for msg in history[-10:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _format_retrieved_documents(
        self, documents: list[dict]
    ) -> str:
        if not documents:
            return "No relevant documents found."
        parts = []
        for i, doc in enumerate(documents[:5], 1):
            text = doc.get("text", "")
            score = doc.get("score", 0)
            parts.append(
                f"[Doc {i}] (relevance: {score:.2f})\n{text[:500]}"
            )
        return "\n\n".join(parts)

    def _build_context_string(
        self, context: dict[str, Any]
    ) -> str:
        if not context:
            return ""

        parts = []

        if "conversation_history" in context:
            history = context["conversation_history"]
            parts.append(
                "Conversation History:\n"
                + self._format_conversation_history(history)
            )

        if "retrieved_documents" in context:
            docs = context["retrieved_documents"]
            parts.append(
                "Relevant Documents:\n"
                + self._format_retrieved_documents(docs)
            )

        if "memory_summary" in context:
            summary = context["memory_summary"]
            if summary:
                parts.append(
                    f"Conversation Summary:\n{summary}"
                )

        return "\n\n".join(parts)
