from datetime import datetime
from typing import Literal, Optional

from beanie import Document
from pydantic import Field


class DocumentMetadata(Document):
    filename: str
    original_name: str
    content_type: str
    file_size: int = 0
    chunk_count: int = 0
    status: Literal["processing", "ready", "failed"] = "processing"
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
    uploaded_by: str
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    class Settings:
        name = "documents"
        indexes = [
            "status",
            "doc_type",
            "uploaded_by",
            "created_at",
        ]
