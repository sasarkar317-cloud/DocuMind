import os
import shutil
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.user import User
from app.rag.ingestion import ingest_document, remove_document_from_vector_store


def upload_document(file: UploadFile, access_level: int, db: Session, user: User):
    ALLOWED_EXTENSIONS = ['.pdf', '.txt']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f'{ext} file not allowed')

    if access_level not in [0, 1, 2]:
        raise HTTPException(status_code=400, detail='Access level must be 0, 1, or 2')

    if user.role == 1 and access_level == 0:
        raise HTTPException(status_code=403, detail='Staff cannot upload admin-only documents')

    if db.query(Document).filter(Document.filename == file.filename).first():
        raise HTTPException(status_code=400, detail='File already exists')

    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, 'wb') as f:
        shutil.copyfileobj(file.file, f)

    new_doc = Document(filename=file.filename, filepath=file_path, access_level=access_level, uploaded_by=user.id)
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    ingest_document(file_path, new_doc.id, access_level)
    return new_doc


def search_document(doc_id: int, db: Session, user: User):
    query = db.query(Document).filter(Document.is_deleted == False, Document.id == doc_id)
    if user.role == 1:
        query = query.filter(Document.access_level != 0)
    doc = query.first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    return doc


def list_all_documents(db: Session, user: User):
    query = db.query(Document).filter(Document.is_deleted == False).order_by(Document.created_at.desc())
    if user.role == 1:
        query = query.filter(Document.access_level != 0)
    docs = query.all()
    if not docs:
        raise HTTPException(status_code=404, detail='No documents found')
    return {'total': query.count(), 'list_documents': docs}


def delete_document(doc_id: int, db: Session):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail='Document not found')

    if os.path.exists(doc.filepath):
        os.remove(doc.filepath)

    db.delete(doc)
    db.commit()

    remove_document_from_vector_store(doc_id)
    return {'message': f'{doc.filename} deleted successfully'}
