import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.inverted_index = {}
        self.doc_freqs = {}

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "out",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
        }
        return [
            t for t in tokens if t not in stop_words
        ]

    def index_documents(
        self, documents: List[Dict[str, Any]]
    ):
        self.documents = documents
        self.doc_lengths = []
        self.inverted_index = {}
        self.doc_freqs = {}

        for doc_idx, doc in enumerate(documents):
            text = doc.get("text", "")
            tokens = self._tokenize(text)
            self.doc_lengths.append(len(tokens))

            unique_tokens = set(tokens)
            for token in unique_tokens:
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append(doc_idx)

                if token not in self.doc_freqs:
                    self.doc_freqs[token] = 0
                self.doc_freqs[token] += 1

        if self.doc_lengths:
            self.avg_doc_length = sum(
                self.doc_lengths
            ) / len(self.doc_lengths)
        else:
            self.avg_doc_length = 0

        logger.info(
            f"Indexed {len(documents)} documents for BM25"
        )

    def search(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        query_tokens = self._tokenize(query)
        n_docs = len(self.documents)

        scores = [0.0] * n_docs

        for token in query_tokens:
            if token not in self.inverted_index:
                continue

            doc_indices = self.inverted_index[token]
            df = self.doc_freqs.get(token, 0)
            idf = math.log(
                (n_docs - df + 0.5) / (df + 0.5) + 1
            )

            for doc_idx in doc_indices:
                doc_tokens = self._tokenize(
                    self.documents[doc_idx].get("text", "")
                )
                tf = doc_tokens.count(token)
                doc_len = self.doc_lengths[doc_idx]

                tf_norm = (
                    tf
                    * (self.k1 + 1)
                    / (
                        tf
                        + self.k1
                        * (
                            1
                            - self.b
                            + self.b
                            * doc_len
                            / self.avg_doc_length
                        )
                    )
                )

                scores[doc_idx] += idf * tf_norm

        scored_docs = [
            (idx, score)
            for idx, score in enumerate(scores)
            if score > 0
        ]
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_docs[:top_k]:
            result = self.documents[idx].copy()
            result["bm25_score"] = score
            results.append(result)

        return results
