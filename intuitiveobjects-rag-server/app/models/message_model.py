from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class Message(BaseModel):
    chat_id: str
    content: str
    role: str
    rating: Optional[float] = Field(default=0.0, ge=0.0, lt=5.0)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())
