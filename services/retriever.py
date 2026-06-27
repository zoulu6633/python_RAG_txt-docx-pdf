from langchain_core.documents import Document
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from pathlib import Path
from models import ChatMessage, SourceChunk
from services.files import vectorstore
from llm import build_retrieval_queries

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# 加载重排模型
rerank_model = HuggingFaceCrossEncoder(
    model_name="BAAI/bge-reranker-base"
)

# 定义重排器，只保留前 5
compressor = CrossEncoderReranker(
    model=rerank_model,
    top_n=5
)

# 构建搜索参数
def build_search_kwargs(
    file_ids: list[str] | None = None,
    category_ids: list[str] | None = None
):
    search_kwargs = {"k": 10}
    filters = []

    if file_ids:
        if len(file_ids) == 1:
            filters.append({"file_id": file_ids[0]})
        else:
            filters.append({"file_id": {"$in": file_ids}})

    if category_ids:
        if len(category_ids) == 1:
            filters.append({"category_id": category_ids[0]})
        else:
            filters.append({"category_id": {"$in": category_ids}})

    if len(filters) == 1:
        search_kwargs["filter"] = filters[0]
    elif len(filters) > 1:
        search_kwargs["filter"] = {"$and": filters}

    return search_kwargs

# 构建基础检索器
def build_retriever(
    file_ids: list[str] | None = None,
    category_ids: list[str] | None = None
):
    base_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=build_search_kwargs(file_ids, category_ids)
    )

    return base_retriever

# 去重
def deduplicate_documents(documents: list[Document]) -> list[Document]:
    unique_documents: list[Document] = []
    seen_keys: set[str] = set()

    for document in documents:
        metadata = document.metadata or {}
        key = metadata.get("chunk_id") or f"{metadata.get('file_id', '')}:{document.page_content}"

        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_documents.append(document)

    return unique_documents

# 检索文档
def retrieve_documents(
    query: str,
    file_ids: list[str] | None = None,
    category_ids: list[str] | None = None,
    history_messages: list[ChatMessage] | None = None
) -> list[Document]:
    retriever = build_retriever(file_ids, category_ids)

    search_queries = build_retrieval_queries(query, history_messages)

    candidates: list[Document] = []
    for search_query in search_queries:
        docs = retriever.invoke(search_query)
        candidates.extend(docs)

    unique_candidates = deduplicate_documents(candidates)
    if not unique_candidates:
        return []

    # 用去重后的文档作为重排 query
    rerank_query = search_queries[0] if search_queries else query
    reranked_results = compressor.compress_documents(
        unique_candidates,
        query=rerank_query
    )

    return list(reranked_results)

# 序列化文档
def serialize_documents(documents: list[Document]) -> list[SourceChunk]:
    serialized: list[SourceChunk] = []

    for document in documents:
        metadata = document.metadata or {}
        content = document.page_content.strip()
        if not content:
            continue

        serialized.append(
            SourceChunk(
                file_id=metadata.get("file_id", ""),
                file_name=metadata.get("file_name", "未知文件"),
                chunk_id=metadata.get("chunk_id", ""),
                user_id=metadata.get("user_id", ""),
                content=content,
            )
        )

    return serialized

def get_chunk(query: str, file_ids: list[str] | None = None, category_ids: list[str] | None = None):
    retriever_results = retrieve_documents(query, file_ids, category_ids)
    return serialize_documents(retriever_results)