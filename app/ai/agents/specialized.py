import logging
from typing import Any

from app.ai.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class RAGRetrievalAgent(BaseAgent):
    """Retrieves relevant documents using hybrid search."""

    def __init__(self):
        super().__init__(
            name="rag_retrieval",
            description="Retrieves relevant documents from knowledge base",
        )

    def get_system_prompt(self) -> str:
        return ""

    def get_user_prompt(
        self, message: str, context: dict[str, Any] = None
    ) -> str:
        return ""

    async def process(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        try:
            from app.ai.rag.hybrid import (
                HybridSearchService,
            )

            search_service = HybridSearchService()

            session_id = (
                context.get("session_id", "")
                if context
                else ""
            )

            results = await search_service.search(
                query=message,
                top_k=5,
            )

            logger.info(
                f"RAG retrieved {len(results)} documents for query"
            )

            return {
                "documents": results,
                "count": len(results),
                "agent": self.name,
            }

        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return {
                "documents": [],
                "count": 0,
                "agent": self.name,
                "error": str(e),
            }


class ConversationMemoryAgent(BaseAgent):
    """Manages conversation memory and context."""

    def __init__(self):
        super().__init__(
            name="memory",
            description="Manages conversation context and memory",
        )

    def get_system_prompt(self) -> str:
        return """You are a conversation memory agent. Summarize the conversation history to provide context for other agents."""

    def get_user_prompt(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> str:
        history = context.get("conversation_history", []) if context else []
        return f"Summarize this conversation:\n\n{self._format_conversation_history(history)}"

    async def process(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        try:
            from app.ai.memory.conversation import (
                ConversationMemory,
            )

            memory = ConversationMemory()
            session_id = (
                context.get("session_id", "")
                if context
                else ""
            )

            if session_id:
                history = await memory.get_history(
                    session_id
                )
            else:
                history = []

            summary = await memory.summarize(
                history
                + [{"role": "user", "content": message}]
            )

            return {
                "history": history,
                "summary": summary,
                "agent": self.name,
            }

        except Exception as e:
            logger.error(f"Memory agent error: {e}")
            return {
                "history": [],
                "summary": "",
                "agent": self.name,
                "error": str(e),
            }


class ResponseValidationAgent(BaseAgent):
    """Validates and filters AI responses."""

    def __init__(self):
        super().__init__(
            name="validation",
            description="Validates response quality and safety",
        )

    def get_system_prompt(self) -> str:
        return """You are a response validation agent. Review the AI response for quality, accuracy, and safety.

Quality Criteria:
1. Relevance: Directly addresses the user's query
2. Accuracy: Information is factually correct
3. Completeness: Comprehensive answer
4. Tone: Professional and empathetic
5. Safety: No harmful or inappropriate content
6. Clarity: Easy to understand

If the response has issues, provide an improved version.
If the response is good, return it as-is."""

    def get_user_prompt(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> str:
        return message

    async def process(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        response = (
            context.get("response", "") if context else ""
        )
        agent_type = (
            context.get("agent_type", "general")
            if context
            else "general"
        )

        is_valid = True
        issues = []

        if len(response.strip()) < 10:
            is_valid = False
            issues.append("Response too short")

        if len(response) > 4000:
            response = response[:4000] + "..."

        lower_response = response.lower()
        uncertain_phrases = [
            "i don't know",
            "i'm not sure",
            "i cannot help",
            "as an ai",
        ]
        for phrase in uncertain_phrases:
            if phrase in lower_response:
                issues.append(
                    f"Contains uncertain phrase: {phrase}"
                )

        if not any(c.isalnum() for c in response):
            is_valid = False
            issues.append("No text content")

        return {
            "response": response,
            "is_valid": is_valid,
            "issues": issues,
            "agent": self.name,
        }
