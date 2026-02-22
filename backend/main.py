from fastapi import FastAPI, APIRouter
from app.api import auth, documents, chat
from app.db.init_db import prepare_database
from app.rag.vector_store import all_docs

app = FastAPI(title="DocuMind - Document Management System", version="1.0.0")

# Create DB tables and seed default users on startup
prepare_database()

app.include_router(router=auth.router, prefix='/auth', tags=['Authentication'])
app.include_router(router=documents.router, prefix='/doc', tags=['Documents'])
app.include_router(router=chat.router, prefix='/chat', tags=['Chatting'])

# Test endpoint
test_router = APIRouter()

@test_router.get('/show_all_docs')
def show_all_docs():
    return all_docs()

app.include_router(router=test_router, prefix='/test', tags=['Test'])
