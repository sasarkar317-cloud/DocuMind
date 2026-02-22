from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.schemas.chat import ChatMessageCreate
from app.rag.retrieval import retrieve_answer


def create_chat_session_helper(user: User, db: Session):
    chat_session = ChatSession(user_id=user.id)
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def get_user_access_levels(user: User):
    if user.role == 0:
        return [0, 1, 2]
    if user.role == 1:
        return [1, 2]
    return [2]


def send_chat_message_helper(session_id, message: ChatMessageCreate, db: Session, current_user):
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail='Chat session not found')

    question = message.content.strip()

    user_message = ChatMessage(session_id=session_id, role=0, context=question)
    db.add(user_message)
    db.commit()

    allowed_levels = get_user_access_levels(current_user)

    try:
        answer = retrieve_answer(question, allowed_levels)
    except Exception as e:
        answer = f'Sorry, I got an error: {str(e)}'

    ai_message = ChatMessage(session_id=session_id, role=1, context=answer)
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return ai_message


def get_chat_sessions_helper(user_id: int, db: Session, current_user: User):
    if user_id is not None:
        if current_user.role != 0:
            raise HTTPException(status_code=403, detail="Only admin can view other users' sessions")
        target_user_id = user_id
    else:
        target_user_id = current_user.id

    return db.query(ChatSession).filter(
        ChatSession.user_id == target_user_id
    ).order_by(ChatSession.created_at.desc()).all()


def get_chat_history_helper(session_id: int, db: Session, current_user: User):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail='Chat session not found')

    if current_user.role != 0 and chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='You can only view your own chat history')

    return db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()


def delete_chat_session_helper(session_id: int, db: Session, current_user: User):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail='Chat session not found')

    if current_user.role != 0 and session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail='You can only delete your own chat sessions')

    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()

    return {'message': f'Chat session {session_id} deleted successfully'}


def get_all_sessions_helper(db: Session, current_user: User):
    if current_user.role != 0:
        raise HTTPException(status_code=403, detail='Admin privileges required')

    users = db.query(User).filter(User.is_deleted == False).all()
    result = []
    for user in users:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user.id
        ).order_by(ChatSession.created_at.desc()).all()

        result.append({
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'session_count': len(sessions),
            'sessions': [
                {
                    'id': s.id,
                    'created_at': s.created_at,
                    'message_count': db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
                }
                for s in sessions
            ]
        })
    return result
