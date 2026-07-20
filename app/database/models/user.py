from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import EmailStr, Field


class User(Document):
    full_name: str
    email: EmailStr
    password_hash: str

    role: Literal["user", "admin"] = "user"

    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)

    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"