from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    success: bool = True
    message: str = ""
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
