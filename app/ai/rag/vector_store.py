import logging
import os
import pickle
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

VECTOR_STORE_DIR = "data/vector_store"


class VectorStoreService:
    def __init__(self):
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        self.index_path = os.path.join(
            VECTOR_STORE_DIR, "faiss.index"
        )
        self.metadata_path = os.path.join(
            VECTOR_STORE_DIR, "metadata.pkl"
        )
        self.index = None
        self.documents = []
        self.ids = []
        self._load()

    def _load(self):
        try:
            import faiss

            if os.path.exists(self.index_path):
                self.index = faiss.read_index(
                    self.index_path
                )
                if os.path.exists(self.metadata_path):
                    with open(
                        self.metadata_path, "rb"
                    ) as f:
                        data = pickle.load(f)
                        self.documents = data.get(
                            "documents", []
                        )
                        self.ids = data.get("ids", [])
                logger.info(
                    f"Loaded vector store with {self.index.ntotal} vectors"
                )
            else:
                self.index = None
                logger.info("No existing vector store found")

        except ImportError:
            logger.warning(
                "faiss not available, using in-memory store"
            )
            self.index = None

    def _save(self):
        try:
            import faiss

            if self.index is not None:
                faiss.write_index(
                    self.index, self.index_path
                )
                with open(
                    self.metadata_path, "wb"
                ) as f:
                    pickle.dump(
                        {
                            "documents": self.documents,
                            "ids": self.ids,
                        },
                        f,
                    )
                logger.info("Vector store saved")

        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[Dict[str, Any]],
    ):
        if not ids or not embeddings or not documents:
            logger.warning("add_documents called with empty data, skipping")
            return

        try:
            import faiss

            vectors = np.array(
                embeddings, dtype=np.float32
            )

            if self.index is None:
                dimension = vectors.shape[1]
                self.index = faiss.IndexFlatIP(dimension)

            faiss.normalize_L2(vectors)
            self.index.add(vectors)

            self.ids.extend(ids)
            self.documents.extend(documents)

            self._save()

            logger.info(
                f"Added {len(ids)} documents to vector store"
            )

        except Exception as e:
            logger.error(
                f"Error adding documents: {e}"
            )
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        try:
            if (
                self.index is None
                or self.index.ntotal == 0
            ):
                return []

            query_vector = np.array(
                [query_embedding], dtype=np.float32
            )

            import faiss

            faiss.normalize_L2(query_vector)

            k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(
                query_vector, k
            )

            results = []
            for dist, idx in zip(
                distances[0], indices[0]
            ):
                if idx < len(self.documents):
                    result = self.documents[idx].copy()
                    result["score"] = float(dist)
                    result["id"] = self.ids[idx]
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def delete_by_document(
        self, document_id: str
    ) -> int:
        try:
            indices_to_keep = []
            for i, doc in enumerate(self.documents):
                if doc.get("metadata", {}).get(
                    "document_id"
                ) != document_id:
                    indices_to_keep.append(i)

            removed_count = (
                len(self.documents) - len(indices_to_keep)
            )

            if removed_count > 0:
                self.documents = [
                    self.documents[i] for i in indices_to_keep
                ]
                self.ids = [
                    self.ids[i] for i in indices_to_keep
                ]

                if self.documents:
                    import faiss

                    embeddings = []
                    for doc in self.documents:
                        embeddings.append(
                            doc.get("embedding", [0] * 384)
                        )

                    vectors = np.array(
                        embeddings, dtype=np.float32
                    )
                    dimension = vectors.shape[1]
                    self.index = faiss.IndexFlatIP(dimension)
                    faiss.normalize_L2(vectors)
                    self.index.add(vectors)
                else:
                    self.index = None

                self._save()

            return removed_count

        except Exception as e:
            logger.error(
                f"Error deleting documents: {e}"
            )
            return 0

    def get_stats(self) -> dict:
        return {
            "total_vectors": (
                self.index.ntotal if self.index else 0
            ),
            "total_documents": len(self.documents),
        }
