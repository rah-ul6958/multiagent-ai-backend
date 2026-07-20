from typing import Any

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)

from app.ai.agents.base import BaseAgent
from app.ai.llm.service import llm_service


class IntentDetectionAgent(BaseAgent):
    """Detects user intent using LLM for accurate classification."""

    INTENTS = [
        "billing",
        "technical_support",
        "product",
        "complaint",
        "faq",
    ]

    def __init__(self):
        super().__init__(
            name="intent_detection",
            description="Classifies user intent from messages",
        )

    def get_system_prompt(self) -> str:
        return """You are an intent classification system. Your ONLY job is to analyze the user's message and classify it into exactly one category.

Categories:
- billing: Payment issues, invoices, refunds, subscriptions, charges, pricing questions
- technical_support: Bugs, errors, crashes, installation, troubleshooting, configuration issues
- product: Product information, features, specifications, comparisons, availability, recommendations
- complaint: Dissatisfaction, negative feedback, escalation requests, frustration, anger
- faq: General questions, how-to guides, information requests, documentation questions

You MUST respond with ONLY a JSON object in this exact format:
{"intent": "<category>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}

Do NOT add any other text, explanation, or formatting. Just the JSON."""

    def get_user_prompt(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> str:
        return f"Classify this user message:\n\n\"{message}\""

    async def process(
        self,
        message: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        import json

        system_prompt = self.get_system_prompt()
        user_prompt = self.get_user_prompt(message, context)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        result = await llm_service.invoke_with_metadata(
            messages, temperature=0.1
        )

        content = result["content"]

        try:
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            parsed = json.loads(content)
            intent = parsed.get("intent", "faq")
            confidence = float(
                parsed.get("confidence", 0.5)
            )
        except (json.JSONDecodeError, ValueError):
            intent = self._fallback_classify(message)
            confidence = 0.4

        if intent not in self.INTENTS:
            intent = "faq"
            confidence = 0.3

        return {
            "intent": intent,
            "confidence": confidence,
            "agent": self.name,
            "provider": result.get("provider", "unknown"),
        }

    def _fallback_classify(self, message: str) -> str:
        keywords = {
            "billing": [
                "bill", "charge", "payment", "invoice",
                "refund", "subscription", "price", "cost",
            ],
            "technical_support": [
                "error", "bug", "crash", "not working",
                "broken", "fix", "install", "setup",
            ],
            "product": [
                "product", "feature", "specification",
                "compare", "recommend", "available",
            ],
            "complaint": [
                "complaint", "unhappy", "terrible",
                "worst", "disappointed", "frustrated",
            ],
            "faq": [
                "how to", "what is", "where", "when",
                "can i", "tell me",
            ],
        }

        message_lower = message.lower()
        scores = {}
        for intent, words in keywords.items():
            scores[intent] = sum(
                1 for w in words if w in message_lower
            )

        return max(scores, key=scores.get) if scores else "faq"
