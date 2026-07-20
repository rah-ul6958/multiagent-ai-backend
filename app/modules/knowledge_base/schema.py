from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class UploadDocumentRequest(BaseModel):
    doc_type: Literal[
        "faq",
        "refund_policy",
        "warranty",
        "shipping_policy",
        "pricing",
        "product_catalog",
        "installation_guide",
        "user_manual",
        "general",
    ] = "general"
    metadata: dict = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    content_type: str
    file_size: int
    chunk_count: int
    status: str
    doc_type: str
    uploaded_by: str
    created_at: datetime
    error_message: Optional[str] = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class ReindexRequest(BaseModel):
    document_id: Optional[str] = None
    full_reindex: bool = False


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    doc_type: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    content: str
    score: float
    source: str
    doc_type: str
    metadata: dict = Field(default_factory=dict)
