import logging
import os
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Centralized LLM service with provider fallback."""

    def __init__(self):
        self._primary_llm: Optional[BaseChatModel] = None
        self._fallback_llm: Optional[BaseChatModel] = None
        self._openrouter_llm: Optional[BaseChatModel] = None

    def _get_primary_llm(self) -> BaseChatModel:
        if self._primary_llm is None:
            api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
            if not api_key:
                raise ValueError("No primary API key available")

            try:
                from langchain_groq import ChatGroq

                self._primary_llm = ChatGroq(
                    model=settings.AI_PRIMARY_MODEL,
                    groq_api_key=api_key,
                    temperature=0.7,
                    max_tokens=2048,
                    timeout=30,
                )
                logger.info(
                    f"Initialized primary LLM (Groq): {settings.AI_PRIMARY_MODEL}"
                )
            except Exception as e:
                logger.error(f"Failed to init primary LLM: {e}")
                raise
        return self._primary_llm

    def _get_fallback_llm(self) -> BaseChatModel:
        if self._fallback_llm is None:
            api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError("No fallback API key available")

            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                self._fallback_llm = ChatGoogleGenerativeAI(
                    model=settings.AI_FALLBACK_MODEL,
                    google_api_key=api_key,
                    temperature=0.7,
                    max_output_tokens=2048,
                    convert_system_message_to_human=True,
                )
                logger.info(
                    f"Initialized fallback LLM (Gemini): {settings.AI_FALLBACK_MODEL}"
                )
            except Exception as e:
                logger.error(f"Failed to init fallback LLM: {e}")
                raise
        return self._fallback_llm

    def _get_openrouter_llm(self) -> Optional[BaseChatModel]:
        if self._openrouter_llm is None:
            api_key = settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
            if not api_key:
                return None
            try:
                from langchain_openai import ChatOpenAI

                self._openrouter_llm = ChatOpenAI(
                    model="anthropic/claude-3-haiku",
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=0.7,
                    max_tokens=2048,
                )
                logger.info("Initialized OpenRouter LLM")
            except Exception as e:
                logger.warning(f"Failed to init OpenRouter: {e}")
        return self._openrouter_llm

    async def invoke(
        self,
        messages: list[BaseMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Invoke LLM with automatic fallback."""
        try:
            llm = self._get_primary_llm()
            llm.temperature = temperature
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.warning(f"Primary LLM failed: {e}")

        try:
            llm = self._get_fallback_llm()
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.warning(f"Fallback LLM failed: {e}")

        openrouter = self._get_openrouter_llm()
        if openrouter:
            try:
                response = await openrouter.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.error(f"OpenRouter also failed: {e}")

        return "I apologize, but I'm experiencing technical difficulties. Please try again later."

    async def invoke_with_metadata(
        self,
        messages: list[BaseMessage],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Invoke LLM and return response with metadata."""
        provider = "unknown"
        model = "unknown"

        try:
            llm = self._get_primary_llm()
            provider = "groq"
            model = settings.AI_PRIMARY_MODEL
            response = await llm.ainvoke(messages)
            return {
                "content": response.content,
                "provider": provider,
                "model": model,
                "usage": getattr(response, "usage_metadata", {}),
            }
        except Exception as e:
            logger.warning(f"Primary (Groq) failed: {e}")

        try:
            llm = self._get_fallback_llm()
            provider = "gemini"
            model = settings.AI_FALLBACK_MODEL
            response = await llm.ainvoke(messages)
            return {
                "content": response.content,
                "provider": provider,
                "model": model,
                "usage": getattr(response, "usage_metadata", {}),
            }
        except Exception as e:
            logger.warning(f"Fallback (Gemini) failed: {e}")

        openrouter = self._get_openrouter_llm()
        if openrouter:
            try:
                provider = "openrouter"
                model = "claude-3-haiku"
                response = await openrouter.ainvoke(messages)
                return {
                    "content": response.content,
                    "provider": provider,
                    "model": model,
                    "usage": {},
                }
            except Exception as e:
                logger.error(f"OpenRouter failed: {e}")

        return {
            "content": "I apologize, but I'm experiencing technical difficulties.",
            "provider": "none",
            "model": "none",
            "usage": {},
        }

    async def stream(
        self,
        messages: list[BaseMessage],
        temperature: float = 0.7,
    ):
        """Stream LLM response tokens."""
        try:
            llm = self._get_primary_llm()
            llm.temperature = temperature
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield {"content": chunk.content, "provider": "groq"}
            return
        except Exception as e:
            logger.warning(f"Primary streaming failed: {e}")

        try:
            llm = self._get_fallback_llm()
            async for chunk in llm.astream(messages):
                if chunk.content:
                    yield {"content": chunk.content, "provider": "gemini"}
            return
        except Exception as e:
            logger.error(f"Fallback streaming failed: {e}")

        yield {"content": "I apologize, but I'm experiencing technical difficulties.", "provider": "none"}


llm_service = LLMService()
