from __future__ import annotations

from langchain_core.documents import Document

from schemas import ChatMessage, SourceInfo
from services.llm import build_retrieval_queries
from services.vector_store import compressor, vectorstore


def _build_search_kwargs(
    knowledge_base_id: str | None = None,
) -> dict:
    search_kwargs: dict = {"k": 10}

    if knowledge_base_id:
        search_kwargs["filter"] = {"knowledge_base_id": knowledge_base_id}

    return search_kwargs


def _deduplicate_documents(documents: list[Document]) -> list[Document]:
    unique: list[Document] = []
    seen: set[str] = set()

    for doc in documents:
        meta = doc.metadata or {}
        key = meta.get("chunk_id") or f"{meta.get('document_id', '')}:{doc.page_content}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(doc)

    return unique


def retrieve_documents(
    query: str,
    knowledge_base_id: str | None = None,
    history_messages: list[ChatMessage] | None = None,
) -> list[Document]:
    search_kwargs = _build_search_kwargs(knowledge_base_id)

    search_queries = build_retrieval_queries(query, history_messages)

    candidates: list[Document] = []
    for sq in search_queries:
        results = vectorstore.similarity_search_with_score(
            query=sq,
            k=search_kwargs["k"],
            filter=search_kwargs.get("filter"),
        )
        for doc, score in results:
            doc.metadata["similarity_score"] = score
            candidates.append(doc)

    unique_candidates = _deduplicate_documents(candidates)
    if not unique_candidates:
        return []

    rerank_query = search_queries[0] if search_queries else query
    reranked_results = compressor.compress_documents(unique_candidates, query=rerank_query)
    return list(reranked_results)


def serialize_sources(documents: list[Document]) -> list[SourceInfo]:
    serialized: list[SourceInfo] = []
    for doc in documents:
        meta = doc.metadata or {}
        content = doc.page_content.strip()
        if not content:
            continue
        score = meta.get("relevance_score") or meta.get("similarity_score", 0.0)
        serialized.append(SourceInfo(
            document_id=meta.get("document_id", ""),
            title=meta.get("document_name", "未知文档"),
            chunk_id=meta.get("chunk_id", ""),
            knowledge_base_name=meta.get("knowledge_base_name", ""),
            score=float(score),
            content=content,
        ))
    return serialized


def format_context(documents: list[Document]) -> str:
    blocks: list[str] = []
    for idx, doc in enumerate(documents, start=1):
        content = doc.page_content.strip()
        if not content:
            continue
        meta = doc.metadata or {}
        source = f"文档: {meta.get('document_name', '未知')}"
        if meta.get("chunk_id"):
            source += f" | 片段: {meta['chunk_id']}"
        blocks.append(f"[参考片段 {idx}]\n{source}\n{content}")
    return "\n\n".join(blocks)
