import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_chroma import Chroma

_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
        )
        _vector_store = Chroma(
            collection_name='company_documents',
            embedding_function=embeddings,
            persist_directory='chroma_db'
        )
    return _vector_store

def all_docs():
    results = get_vector_store().get(include=["documents", "metadatas"])
    documents = [
        {"content": content, "metadata": metadata}
        for content, metadata in zip(results["documents"], results["metadatas"])
    ]
    return {"total": len(documents), "documents": documents}
