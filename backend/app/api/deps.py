from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt
from app.db.session import get_db
from app.models.user import User
from app.core.config import SECRET_KEY


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = jwt.decode(token=token, key=SECRET_KEY, algorithms=['HS256'])
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid token payload')
    user = db.query(User).filter(User.id == user_id, User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user


def require_admin(user: User = Depends(get_current_user)):
    if user.role != 0:
        raise HTTPException(status_code=403, detail='Admin access required')
    return user


def require_admin_staff(user: User = Depends(get_current_user)):
    if user.role not in [0, 1]:
        raise HTTPException(status_code=403, detail='Admin or Staff access required')
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.is_deleted:
        raise HTTPException(status_code=403, detail='User account has been deactivated')
    return current_user
