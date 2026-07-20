import logging
from typing import List

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Lightweight embedding service using multiple backends."""

    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self._embedder = None
        self._backend = None

    def _init_embedder(self):
        """Try backends in order: fastembed, sklearn fallback."""
        # Try fastembed with supported model
        try:
            from fastembed import TextEmbedding

            self._embedder = TextEmbedding(
                model_name="BAAI/bge-small-en-v1.5"
            )
            self._backend = "fastembed"
            self.model_name = "BAAI/bge-small-en-v1.5"
            logger.info(
                f"Loaded embedding model (fastembed): {self.model_name}"
            )
            return
        except Exception as e:
            logger.warning(f"fastembed failed: {e}")

        # Fallback: TF-IDF vectorizer (no model download needed)
        try:
            from sklearn.feature_extraction.text import (
                TfidfVectorizer,
            )
            import numpy as np

            self._embedder = TfidfVectorizer(
                max_features=384,
                stop_words="english",
            )
            self._backend = "tfidf"
            logger.info(
                "Using TF-IDF fallback for embeddings"
            )
            return
        except ImportError:
            logger.warning("sklearn not available")

        # Last resort: random projections (for testing)
        self._backend = "random"
        logger.warning(
            "Using random embeddings (for testing only)"
        )

    async def embed_query(self, text: str) -> List[float]:
        if self._embedder is None:
            self._init_embedder()

        if self._backend == "fastembed":
            embeddings = list(
                self._embedder.embed([text])
            )
            return embeddings[0].tolist()

        elif self._backend == "tfidf":
            import numpy as np

            try:
                vec = self._embedder.transform([text])
                return vec.toarray()[0].tolist()
            except Exception:
                self._embedder.fit([text])
                vec = self._embedder.transform([text])
                return vec.toarray()[0].tolist()

        else:
            import hashlib
            import struct

            h = hashlib.md5(text.encode()).digest()
            return [
                struct.unpack("f", h[i : i + 4])[0]
                for i in range(0, min(len(h), 384), 4)
            ] + [0.0] * (384 - min(len(h) // 4, 96))

    async def embed_documents(
        self, texts: List[str]
    ) -> List[List[float]]:
        if self._embedder is None:
            self._init_embedder()

        if self._backend == "fastembed":
            embeddings = list(
                self._embedder.embed(texts)
            )
            return [e.tolist() for e in embeddings]

        elif self._backend == "tfidf":
            import numpy as np

            try:
                vecs = self._embedder.transform(texts)
                return vecs.toarray().tolist()
            except Exception:
                self._embedder.fit(texts)
                vecs = self._embedder.transform(texts)
                return vecs.toarray().tolist()

        else:
            return [
                await self.embed_query(t) for t in texts
            ]
