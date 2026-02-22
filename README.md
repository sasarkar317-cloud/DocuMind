# DocuMind - Document Management System

A FastAPI + Streamlit Document Management System with RAG (Retrieval-Augmented Generation).
Uses SQLite as the database and HuggingFace API for embeddings.

## Project Structure

```
documind/
├── runtime.txt          ← Forces Python 3.11 on Render
├── backend/
│   ├── app/
│   │   ├── api/         ← Route handlers
│   │   ├── core/        ← Config, JWT security
│   │   ├── db/          ← SQLite session & init
│   │   ├── models/      ← SQLAlchemy models
│   │   ├── rag/         ← Vector store, ingestion, retrieval
│   │   ├── schemas/     ← Pydantic schemas
│   │   └── services/    ← Business logic
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
└── frontend/
    ├── streamlit_frontend.py
    └── requirements.txt
```

## Local Setup

```bash
# Backend
cd documind/backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Edit .env with your credentials
uvicorn main:app --reload

# Frontend (new terminal)
cd documind/frontend
pip install -r requirements.txt
streamlit run streamlit_frontend.py
```

## Render Deployment

### Backend
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add all env variables from `.env.example`
- Set `DATABASE_URL=sqlite:///./dms.db`

### Frontend
- Root Directory: `frontend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `streamlit run streamlit_frontend.py --server.port $PORT --server.address 0.0.0.0`
- Update `API_BASE_URL` in `streamlit_frontend.py` to your deployed backend URL

## Roles

| Role  | Value | Access |
|-------|-------|--------|
| Admin | 0     | Everything |
| Staff | 1     | Upload + view staff/public docs |
| User  | 2     | Chat with public docs only |

## Document Access Levels

| Level | Who Sees It |
|-------|-------------|
| 0     | Admin only |
| 1     | Admin + Staff |
| 2     | Everyone |
