from pydantic import BaseModel
from datetime import datetime
from typing import List


class DocumentOut(BaseModel):
    id: int
    filename: str
    filepath: str
    access_level: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


class DocumentListOut(BaseModel):
    total: int
    list_documents: List[DocumentOut]
