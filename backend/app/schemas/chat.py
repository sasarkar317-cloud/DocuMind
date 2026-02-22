from pydantic import BaseModel, field_validator
from datetime import datetime


class ChatSessionOut(BaseModel):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('message cannot be empty')
        return v.strip()


class ChatMessageOut(BaseModel):
    id: int
    role: int
    content: str
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True
