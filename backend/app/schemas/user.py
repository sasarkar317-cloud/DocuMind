from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    email: str
    password: str
    role: int


class UserOut(BaseModel):
    id: int
    email: str
    role: int
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True
