from app.db.session import Base
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from datetime import datetime


class ChatSession(Base):
    __tablename__ = 'chat_session'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = 'chat_message'

    id = Column(Integer, primary_key=True)
    role = Column(Integer, nullable=False)      # 0-human  1-ai  2-system
    context = Column(Text, nullable=False)

    session_id = Column(Integer, ForeignKey('chat_session.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
