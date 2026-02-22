from app.db.session import engine, Base, Local_session
from app.core.config import (
    INITIAL_ADMIN_EMAIL, INITIAL_ADMIN_PASSWORD,
    INITIAL_STAFF_EMAIL, INITIAL_STAFF_PASSWORD,
    INITIAL_USER_EMAIL, INITIAL_USER_PASSWORD
)
from sqlalchemy.orm import Session
from app.models.user import User


def prepare_database():
    """Create tables and seed default users"""
    Base.metadata.create_all(bind=engine)
    seed_initial_users()


def seed_initial_users():
    db: Session = Local_session()
    try:
        if not db.query(User).filter(User.email == INITIAL_ADMIN_EMAIL).first():
            db.add(User(email=INITIAL_ADMIN_EMAIL, password=INITIAL_ADMIN_PASSWORD, role=0, is_deleted=False))

        if not db.query(User).filter(User.email == INITIAL_STAFF_EMAIL).first():
            db.add(User(email=INITIAL_STAFF_EMAIL, password=INITIAL_STAFF_PASSWORD, role=1, is_deleted=False))

        if not db.query(User).filter(User.email == INITIAL_USER_EMAIL).first():
            db.add(User(email=INITIAL_USER_EMAIL, password=INITIAL_USER_PASSWORD, role=2, is_deleted=False))

        db.commit()
    finally:
        db.close()
