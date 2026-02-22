from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.rag.vector_store import get_vector_store


def retrieve_answer(question: str, allowed_levels: list[int]) -> str:
    if not question or not question.strip():
        return "Please provide a valid question"

    access_filter = {"access_level": {"$in": allowed_levels}}
    retriever = get_vector_store().as_retriever(
        search_kwargs={'k': 5, 'filter': access_filter}
    )

    retrieved_docs = retriever.invoke(question)
    if not retrieved_docs:
        return (
            "I don't have enough information in the available documents to answer your question.\n"
            "This could mean:\n"
            "- The information is not in the documents you have access to\n"
            "- The documents haven't been uploaded yet\n"
            "- Try rephrasing your question"
        )

    retrieved_texts = '\n\n'.join(i.page_content for i in retrieved_docs)

    llm = HuggingFaceEndpoint(
        repo_id='mistralai/Mistral-7B-Instruct-v0.2',
        task='text-generation'
    )
    model = ChatHuggingFace(llm=llm)

    prompt = ChatPromptTemplate([
        ("system", """You are a helpful AI assistant for a company's internal documentation system.
Answer questions based ONLY on the provided context from company documents.
Be concise, accurate, and professional. If unsure, say so."""),
        ("human", "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:")
    ])

    return (prompt | model | StrOutputParser()).invoke({
        'context': retrieved_texts,
        'question': question
    })
