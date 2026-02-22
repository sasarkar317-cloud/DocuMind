from datetime import datetime, timedelta
from jose import jwt
from app.core.config import SECRET_KEY


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({'exp': expire})
    return jwt.encode(claims=to_encode, key=SECRET_KEY, algorithm='HS256')
