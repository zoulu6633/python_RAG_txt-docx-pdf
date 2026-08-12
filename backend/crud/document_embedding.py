from __future__ import annotations

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document

from services.vector_store import CHUNK_OVERLAP, splitter, vectorstore


def add_forced_overlap(split_docs: list[Document]) -> list[Document]:
    final_docs: list[Document] = []
    previous_content = ""

    for doc in split_docs:
        content = doc.page_content.strip()
        if not content:
            continue

        if previous_content:
            overlap_text = previous_content[-CHUNK_OVERLAP:]
            if overlap_text and not content.startswith(overlap_text):
                content = overlap_text + content

        final_docs.append(
            Document(
                page_content=content,
                metadata=dict(doc.metadata),
            )
        )
        previous_content = content

    return final_docs


def get_loader(source_path: str):
    if source_path.endswith(".txt"):
        return TextLoader(source_path, encoding="utf-8")
    if source_path.endswith(".pdf"):
        return PyPDFLoader(source_path)
    if source_path.endswith(".docx"):
        return Docx2txtLoader(source_path)
    raise ValueError("不支持的文件类型")


def add_document_chunks(
    source_path: str,
    document_id: str,
    user_id: str,
    document_name: str,
    knowledge_base_id: str,
    knowledge_base_name: str,
) -> int:
    loader = get_loader(source_path)
    docs = loader.load()

    split_docs = splitter.split_documents(docs)
    split_docs = add_forced_overlap(split_docs)

    documents: list[Document] = []
    ids: list[str] = []

    for index, doc in enumerate(split_docs, start=1):
        chunk_id = f"{document_id}_chunk_{index:03d}"
        metadata = {
            "document_id": document_id,
            "document_name": document_name,
            "chunk_id": chunk_id,
            "user_id": user_id,
            "knowledge_base_id": knowledge_base_id,
            "knowledge_base_name": knowledge_base_name,
        }
        documents.append(
            Document(
                page_content=doc.page_content,
                metadata=metadata,
            )
        )
        ids.append(chunk_id)

    vectorstore.add_documents(documents, ids=ids)
    return len(ids)
