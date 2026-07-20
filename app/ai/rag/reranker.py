import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    def __init__(self):
        self.model_name = (
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import (
                    CrossEncoder,
                )

                self._model = CrossEncoder(
                    self.model_name
                )
                logger.info(
                    f"Loaded reranker model: {self.model_name}"
                )
            except Exception as e:
                logger.error(
                    f"Error loading reranker: {e}"
                )
                raise
        return self._model

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []

        try:
            pairs = [
                (query, doc.get("text", ""))
                for doc in documents
            ]

            scores = self.model.predict(pairs)

            for i, doc in enumerate(documents):
                doc["rerank_score"] = float(scores[i])

            reranked = sorted(
                documents,
                key=lambda x: x.get(
                    "rerank_score", 0
                ),
                reverse=True,
            )

            return reranked[:top_k]

        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return documents[:top_k]
