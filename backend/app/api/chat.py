from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.chat import ChatSessionOut, ChatMessageCreate
from app.models.user import User
from app.api.deps import get_current_active_user
from app.services.chat_service import (
    create_chat_session_helper,
    send_chat_message_helper,
    get_chat_sessions_helper,
    get_chat_history_helper,
    delete_chat_session_helper,
    get_all_sessions_helper
)


router = APIRouter()


@router.post('/session', response_model=ChatSessionOut)
def create_chat_session(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return create_chat_session_helper(current_user, db)


@router.post('/session/{session_id}/message')
def send_chat_message(session_id: int, message: ChatMessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return send_chat_message_helper(session_id, message, db, current_user)


@router.get('/sessions')
def get_chat_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user), user_id: int = Query(None)):
    return get_chat_sessions_helper(user_id, db, current_user)


@router.get('/session/{session_id}/history')
def get_chat_history(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return get_chat_history_helper(session_id, db, current_user)


@router.delete('/session/{session_id}')
def delete_chat_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return delete_chat_session_helper(session_id, db, current_user)


@router.get('/admin/all-sessions')
def get_all_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return get_all_sessions_helper(db, current_user)
