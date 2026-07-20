import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from app.core.exceptions import (
    BadRequestError,
    NotFoundError,
)
from app.database.models.document import DocumentMetadata
from app.database.models.user import User
from app.modules.knowledge_base.schema import (
    DocumentListResponse,
    DocumentResponse,
)

logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads/documents"


class KnowledgeBaseService:
    def __init__(self):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    def _doc_to_response(self, doc) -> DocumentResponse:
        return DocumentResponse(
            id=str(doc.id),
            filename=doc.filename,
            original_name=doc.original_name,
            content_type=doc.content_type,
            file_size=doc.file_size,
            chunk_count=doc.chunk_count,
            status=doc.status,
            doc_type=doc.doc_type,
            uploaded_by=doc.uploaded_by,
            created_at=doc.created_at,
            error_message=doc.error_message,
        )

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        doc_type: str,
        user: User,
        metadata: dict = None,
    ) -> DocumentResponse:
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        stored_filename = f"{file_id}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, stored_filename)

        with open(file_path, "wb") as f:
            f.write(file_content)

        doc = DocumentMetadata(
            filename=stored_filename,
            original_name=filename,
            content_type=content_type,
            file_size=len(file_content),
            doc_type=doc_type,
            uploaded_by=str(user.id),
            metadata=metadata or {},
        )

        saved_doc = await doc.insert()

        try:
            from app.ai.rag.loader import PDFLoader
            from app.ai.rag.chunker import DocumentChunker
            from app.ai.rag.embeddings import (
                EmbeddingService,
            )
            from app.ai.rag.vector_store import (
                VectorStoreService,
            )

            loader = PDFLoader()
            documents = loader.load(file_path)

            if not documents:
                saved_doc.chunk_count = 0
                saved_doc.status = "ready"
                saved_doc.error_message = "No extractable text found in PDF (may be image-based)"
                await saved_doc.save()
                logger.warning(
                    f"No text extracted from {filename}"
                )
                return self._doc_to_response(saved_doc)

            chunker = DocumentChunker()
            chunks = chunker.chunk_documents(
                documents,
                metadata={
                    "document_id": str(saved_doc.id),
                    "doc_type": doc_type,
                    "filename": filename,
                },
            )

            if not chunks:
                saved_doc.chunk_count = 0
                saved_doc.status = "ready"
                saved_doc.error_message = "Document loaded but produced no chunks"
                await saved_doc.save()
                return self._doc_to_response(saved_doc)

            embedder = EmbeddingService()
            embeddings = await embedder.embed_documents(
                [c["text"] for c in chunks]
            )

            vector_store = VectorStoreService()
            vector_store.add_documents(
                ids=[c["id"] for c in chunks],
                embeddings=embeddings,
                documents=chunks,
            )

            saved_doc.chunk_count = len(chunks)
            saved_doc.status = "ready"
            await saved_doc.save()

            logger.info(
                f"Document processed: {filename} "
                f"({len(chunks)} chunks)"
            )

        except Exception as e:
            logger.error(f"Document processing error: {e}")
            saved_doc.status = "failed"
            saved_doc.error_message = str(e)
            await saved_doc.save()

        return self._doc_to_response(saved_doc)

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 50,
        doc_type: Optional[str] = None,
    ) -> DocumentListResponse:
        query = {}
        if doc_type:
            query["doc_type"] = doc_type

        documents = (
            await DocumentMetadata.find(query)
            .sort("-created_at")
            .skip(skip)
            .limit(limit)
            .to_list()
        )

        total = await DocumentMetadata.find(query).count()

        return DocumentListResponse(
            documents=[
                self._doc_to_response(d) for d in documents
            ],
            total=total,
        )

    async def get_document(
        self, document_id: str
    ) -> DocumentResponse:
        doc = await DocumentMetadata.get(document_id)
        if not doc:
            raise NotFoundError("Document not found")
        return self._doc_to_response(doc)

    async def delete_document(
        self, document_id: str
    ) -> bool:
        doc = await DocumentMetadata.get(document_id)
        if not doc:
            raise NotFoundError("Document not found")

        file_path = os.path.join(
            UPLOAD_DIR, doc.filename
        )
        if os.path.exists(file_path):
            os.remove(file_path)

        try:
            from app.ai.rag.vector_store import (
                VectorStoreService,
            )

            vector_store = VectorStoreService()
            vector_store.delete_by_document(document_id)
        except Exception as e:
            logger.warning(
                f"Error removing vectors: {e}"
            )

        await doc.delete()
        logger.info(f"Document deleted: {doc.original_name}")
        return True

    async def reindex_documents(
        self,
        document_id: Optional[str] = None,
        full_reindex: bool = False,
    ) -> dict:
        if document_id:
            docs = [
                await DocumentMetadata.get(document_id)
            ]
            if not docs[0]:
                raise NotFoundError("Document not found")
        else:
            docs = await DocumentMetadata.find(
                {"status": "ready"}
            ).to_list()

        reindexed = 0
        for doc in docs:
            try:
                file_path = os.path.join(
                    UPLOAD_DIR, doc.filename
                )
                if not os.path.exists(file_path):
                    continue

                from app.ai.rag.loader import PDFLoader
                from app.ai.rag.chunker import (
                    DocumentChunker,
                )
                from app.ai.rag.embeddings import (
                    EmbeddingService,
                )
                from app.ai.rag.vector_store import (
                    VectorStoreService,
                )

                if full_reindex:
                    vector_store = VectorStoreService()
                    vector_store.delete_by_document(
                        str(doc.id)
                    )

                loader = PDFLoader()
                documents = loader.load(file_path)

                if not documents:
                    doc.chunk_count = 0
                    doc.status = "ready"
                    doc.error_message = "No extractable text found in PDF"
                    await doc.save()
                    reindexed += 1
                    continue

                chunker = DocumentChunker()
                chunks = chunker.chunk_documents(
                    documents,
                    metadata={
                        "document_id": str(doc.id),
                        "doc_type": doc.doc_type,
                        "filename": doc.original_name,
                    },
                )

                if not chunks:
                    doc.chunk_count = 0
                    doc.status = "ready"
                    await doc.save()
                    reindexed += 1
                    continue

                embedder = EmbeddingService()
                embeddings = await embedder.embed_documents(
                    [c["text"] for c in chunks]
                )

                vector_store = VectorStoreService()
                vector_store.add_documents(
                    ids=[c["id"] for c in chunks],
                    embeddings=embeddings,
                    documents=chunks,
                )

                doc.chunk_count = len(chunks)
                doc.status = "ready"
                await doc.save()
                reindexed += 1

            except Exception as e:
                logger.error(
                    f"Reindex error for {doc.original_name}: {e}"
                )
                doc.status = "failed"
                doc.error_message = str(e)
                await doc.save()

        return {
            "reindexed": reindexed,
            "total": len(docs),
        }
