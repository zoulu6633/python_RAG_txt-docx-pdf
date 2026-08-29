from __future__ import annotations

from langchain_core.documents import Document

from schemas import ChatMessage, SourceInfo
from services.llm import build_retrieval_queries
from services.vector_store import rerank_model, vectorstore

RERANK_TOP_N = 5


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


def _rerank_documents(documents: list[Document], query: str) -> list[Document]:
    pairs = [(query, doc.page_content) for doc in documents]
    scores = rerank_model.score(pairs)
    ranked = sorted(
        zip(documents, scores, strict=False),
        key=lambda pair: pair[1],
        reverse=True,
    )
    top_documents: list[Document] = []
    for doc, score in ranked[:RERANK_TOP_N]:
        doc.metadata["relevance_score"] = float(score)
        top_documents.append(doc)
    return top_documents


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
    return _rerank_documents(unique_candidates, rerank_query)


def serialize_sources(documents: list[Document]) -> list[SourceInfo]:
    serialized: list[SourceInfo] = []
    for doc in documents:
        meta = doc.metadata or {}
        content = doc.page_content.strip()
        if not content:
            continue
        relevance = meta.get("relevance_score")
        if relevance is not None:
            score = float(relevance)
        else:
            # 无重排路径：Chroma 返回 L2 距离（越小越好），转为 0~1 相似度统一量纲
            distance = float(meta.get("similarity_score", 0.0))
            score = 1.0 / (1.0 + distance)
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
