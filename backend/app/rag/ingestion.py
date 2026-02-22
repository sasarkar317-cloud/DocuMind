import os
from fastapi import HTTPException
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.vector_store import get_vector_store


def ingest_document(file_path: str, document_id: int, access_level: int) -> None:
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f'Document not found at {file_path}')

    ext = os.path.splitext(file_path)[1].lower()
    loader_map = {'.pdf': PyPDFLoader, '.txt': TextLoader}
    loader_class = loader_map.get(ext)
    if not loader_class:
        raise Exception(f"Unsupported file type: {ext}")

    document = loader_class(file_path).load()
    if not document:
        raise Exception("No content extracted from the document")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        length_function=len
    )
    chunks = splitter.split_documents(documents=document)
    if not chunks:
        raise Exception("No chunks created from document")

    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            "document_id": document_id,
            "access_level": access_level,
            "chunk_index": i,
            "source": file_path
        })

    get_vector_store().add_documents(documents=chunks)


def remove_document_from_vector_store(doc_id: int):
    try:
        get_vector_store().delete(where={'document_id': doc_id})
    except Exception as e:
        raise Exception(f"Failed to remove document from vector store: {str(e)}")
