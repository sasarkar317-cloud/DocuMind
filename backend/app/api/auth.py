from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token
from app.models.user import User
from app.services.auth_service import register_user, login_user
from app.api.deps import require_admin, get_current_active_user


router = APIRouter()


# ============================================
# REGISTER -> PUBLIC USER ONLY
# ============================================
@router.post('/register', response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if user.role != 2:
        raise HTTPException(status_code=403, detail='Public registration allowed only for User role')
    return register_user(user, db)


# ============================================
# LOGIN -> ALL ROLES
# ============================================
@router.post('/login', response_model=Token)
def login(user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login_user(user, db)


# ============================================
# ADMIN -> CREATE STAFF
# ============================================
@router.post('/admin/create-staff', response_model=UserOut)
def register_staff(user: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if user.role != 1:
        raise HTTPException(status_code=403, detail='This endpoint only creates Staff accounts.')
    return register_user(user, db)


# ============================================
# ADMIN -> CREATE ADMIN
# ============================================
@router.post('/admin/create-admin', response_model=UserOut)
def register_admin(user: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if user.role != 0:
        raise HTTPException(status_code=403, detail='This endpoint only creates Admin accounts.')
    return register_user(user, db)


# ============================================
# ADMIN -> LIST ALL USERS
# ============================================
@router.get('/users', response_model=list[UserOut])
def users_list(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    start: int = 0,
    limit: int = 10,
    include_delete: bool = False
):
    query = db.query(User)
    if not include_delete:
        query = query.filter(User.is_deleted == False)
    return query.offset(start).limit(limit).all()


# ============================================
# ADMIN -> DELETE USER
# ============================================
@router.delete('/users/{user_id}')
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail='Cannot delete your own admin account')
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User Not Found')
    if user.is_deleted:
        raise HTTPException(status_code=404, detail='User is already deactivated')
    user.is_deleted = True
    db.commit()
    return {'message': f'{user.email} has been deleted successfully'}


# ============================================
# GET CURRENT USER -> For frontend
# ============================================
@router.get('/me', response_model=UserOut)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
