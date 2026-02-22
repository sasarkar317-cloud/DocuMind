from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL

# SQLite needs check_same_thread=False for FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

Local_session = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    db = Local_session()
    try:
        yield db
    finally:
        db.close()
