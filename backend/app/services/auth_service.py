from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User
from app.core.security import create_access_token


def register_user(user, db: Session):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = User(email=user.email, password=user.password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(user, db: Session):
    existing_user = db.query(User).filter(User.email == user.username).first()
    if not existing_user:
        raise HTTPException(status_code=401, detail='Invalid email')
    if existing_user.is_deleted:
        raise HTTPException(status_code=403, detail='Account has been deactivated')
    if user.password != existing_user.password:
        raise HTTPException(status_code=401, detail='Invalid Password')

    token = create_access_token(data={
        'user_id': existing_user.id,
        'email': existing_user.email,
        'role': existing_user.role
    })
    return {'access_token': token, 'token_type': 'bearer'}
