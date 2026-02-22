from app.db.session import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime


class Document(Base):
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    filepath = Column(String(500), unique=True)
    access_level = Column(Integer)              # 0-admin only  1-admin+staff  2-public

    uploaded_by = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)
