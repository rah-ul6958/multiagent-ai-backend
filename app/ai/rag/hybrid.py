import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HybridSearchService:
    def __init__(self):
        self.dense_weight = 0.6
        self.sparse_weight = 0.4

    async def search(
        self,
        query: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            from app.ai.rag.embeddings import (
                EmbeddingService,
            )
            from app.ai.rag.vector_store import (
                VectorStoreService,
            )

            embedder = EmbeddingService()
            query_embedding = await embedder.embed_query(
                query
            )

            vector_store = VectorStoreService()
            dense_results = vector_store.search(
                query_embedding, top_k=top_k * 2
            )

            sparse_results = self._bm25_search(
                query, top_k * 2
            )

            combined = self._reciprocal_rank_fusion(
                dense_results, sparse_results
            )

            if doc_type:
                combined = [
                    r
                    for r in combined
                    if r.get("doc_type") == doc_type
                    or r.get("metadata", {}).get("doc_type")
                    == doc_type
                ]

            try:
                from app.ai.rag.reranker import (
                    CrossEncoderReranker,
                )

                reranker = CrossEncoderReranker()
                combined = await reranker.rerank(
                    query, combined, top_k=top_k
                )
            except Exception as e:
                logger.warning(
                    f"Reranking failed, using original order: {e}"
                )
                combined = combined[:top_k]

            return combined

        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return []

    def _bm25_search(
        self, query: str, top_k: int
    ) -> List[Dict[str, Any]]:
        try:
            from app.ai.rag.bm25 import BM25Retriever
            from app.ai.rag.vector_store import (
                VectorStoreService,
            )

            vector_store = VectorStoreService()
            if not vector_store.documents:
                return []

            bm25 = BM25Retriever()
            bm25.index_documents(
                vector_store.documents
            )
            return bm25.search(query, top_k)

        except Exception as e:
            logger.error(f"BM25 search error: {e}")
            return []

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict],
        sparse_results: List[Dict],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        scores = {}

        for rank, doc in enumerate(dense_results):
            doc_id = doc.get("id", str(rank))
            if doc_id not in scores:
                scores[doc_id] = {
                    "doc": doc,
                    "score": 0,
                }
            scores[doc_id]["score"] += (
                self.dense_weight
                * (1 / (k + rank + 1))
            )

        for rank, doc in enumerate(sparse_results):
            doc_id = doc.get("id", str(rank))
            if doc_id not in scores:
                scores[doc_id] = {
                    "doc": doc,
                    "score": 0,
                }
            scores[doc_id]["score"] += (
                self.sparse_weight
                * (1 / (k + rank + 1))
            )

        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

        result = []
        for item in sorted_results:
            doc = item["doc"].copy()
            doc["score"] = item["score"]
            result.append(doc)

        return result
