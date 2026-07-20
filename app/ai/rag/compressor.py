import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ContextCompressor:
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length

    async def compress(
        self,
        query: str,
        documents: List[Dict[str, Any]],
    ) -> str:
        if not documents:
            return ""

        context_parts = []
        current_length = 0

        for doc in documents:
            text = doc.get("text", "")
            if not text:
                continue

            if current_length + len(text) > self.max_context_length:
                remaining = (
                    self.max_context_length - current_length
                )
                if remaining > 100:
                    text = text[:remaining] + "..."
                    context_parts.append(text)
                break

            context_parts.append(text)
            current_length += len(text)

        return "\n\n".join(context_parts)

    def extract_key_sentences(
        self,
        text: str,
        max_sentences: int = 5,
    ) -> str:
        import re

        sentences = re.split(
            r"(?<=[.!?])\s+", text
        )

        if len(sentences) <= max_sentences:
            return text

        scored_sentences = []
        for sentence in sentences:
            score = len(sentence.split())
            if any(
                word in sentence.lower()
                for word in [
                    "important",
                    "key",
                    "note",
                    "remember",
                    "critical",
                    "essential",
                ]
            ):
                score *= 2
            scored_sentences.append(
                (sentence, score)
            )

        scored_sentences.sort(
            key=lambda x: x[1], reverse=True
        )

        top_sentences = scored_sentences[
            :max_sentences
        ]
        top_sentences.sort(
            key=lambda x: sentences.index(x[0])
        )

        return " ".join(
            s[0] for s in top_sentences
        )
