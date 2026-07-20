import hashlib
import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = (
            chunk_size or settings.CHUNK_SIZE
        )
        self.chunk_overlap = (
            chunk_overlap or settings.CHUNK_OVERLAP
        )

    def chunk_documents(
        self,
        documents: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        all_chunks = []

        for doc in documents:
            text = doc.get("text", "")
            doc_metadata = {
                **(doc.get("metadata", {})),
                **(metadata or {}),
            }

            chunks = self._split_text(text)

            for i, chunk_text in enumerate(chunks):
                chunk_id = self._generate_id(
                    chunk_text, doc_metadata
                )
                all_chunks.append(
                    {
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            **doc_metadata,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                        },
                    }
                )

        logger.info(
            f"Created {len(all_chunks)} chunks from {len(documents)} documents"
        )
        return all_chunks

    def _split_text(self, text: str) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        chunks = []
        sentences = re.split(
            r"(?<=[.!?])\s+", text
        )

        current_chunk = ""
        for sentence in sentences:
            if (
                len(current_chunk) + len(sentence)
                <= self.chunk_size
            ):
                current_chunk += (
                    " " + sentence
                    if current_chunk
                    else sentence
                )
            else:
                if current_chunk:
                    chunks.append(
                        current_chunk.strip()
                    )
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        if (
            self.chunk_overlap > 0
            and len(chunks) > 1
        ):
            overlapped_chunks = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_words = chunks[i - 1].split()
                overlap_words = prev_words[
                    -self.chunk_overlap :
                ]
                overlapped_chunks.append(
                    " ".join(overlap_words)
                    + " "
                    + chunks[i]
                )
            chunks = overlapped_chunks

        return [
            c for c in chunks if c.strip()
        ]

    def _generate_id(
        self, text: str, metadata: dict
    ) -> str:
        content = (
            text
            + str(metadata.get("document_id", ""))
            + str(metadata.get("chunk_index", 0))
        )
        return hashlib.md5(
            content.encode()
        ).hexdigest()
