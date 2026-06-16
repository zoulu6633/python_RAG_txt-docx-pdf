from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.vectorstores import Chroma
from pathlib import Path
from file_store import count_records_by_saved_path, delete_file_record, get_file_record
from models import ChatResponse, ChunkRecord, ChunkMetadata, SourceChunk, ChatMessage
from llm import get_answer, stream_answer



embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5"
)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="documents"
)

# 加载重排模型
rerank_model = HuggingFaceCrossEncoder(
    model_name="BAAI/bge-reranker-base"
)
# 定义重排器，只保留前 5
compressor = CrossEncoderReranker(
    model=rerank_model,
    top_n=5
)
def build_retriever(
    file_ids: list[str] | None = None,
    category_ids: list[str] | None = None
):
    search_kwargs = {"k": 10}
    filters = []
    # 过滤文件
    if file_ids:
        if len(file_ids) == 1:
            filters.append({"file_id": file_ids[0]})
        else:
            filters.append({"file_id": {"$in": file_ids}})
    # 过滤分类
    if category_ids:
        if len(category_ids) == 1:
            filters.append({"category_id": category_ids[0]})
        else:
            filters.append({"category_id": {"$in": category_ids}})
    
    if len(filters) == 1:
        search_kwargs["filter"] = filters[0]
    elif len(filters) > 1:
        search_kwargs["filter"] = {"$and": filters}
    # 向量库召回 top 10
    base_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )
    # 组合成最终检索器
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )
    return retriever

CHUNK_SIZE = 300
CHUNK_OVERLAP = 80

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=0
)


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


def get_loader(file_path: str):
    if file_path.endswith(".txt"):
        return TextLoader(file_path, encoding="utf-8")
    elif file_path.endswith(".pdf"):
        return PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        return Docx2txtLoader(file_path)
    else:
        raise ValueError("不支持的文件类型")

def add_documents(file_path: str,file_id: str, user_id: str, file_name: str, category_id: str, category_name: str):
    loader = get_loader(file_path)
    docs = loader.load()

    split_docs = splitter.split_documents(docs)
    split_docs = add_forced_overlap(split_docs)

    documents = []
    ids = []
    chunk_records=[]
    for i, doc in enumerate(split_docs, start=1):

        chunk = ChunkRecord(
            id=f"{file_id}_chunk_{i:03d}",
            document=doc.page_content,
            metadata=ChunkMetadata(
                file_id=file_id,
                file_name=file_name,
                chunk_id=f"{file_id}_chunk_{i:03d}",
                user_id=user_id,
                category_id=category_id,
                category_name=category_name
            )
        )
        chunk_records.append(chunk)

    for chunk in chunk_records:
        documents.append(
            Document(
                page_content=chunk.document,
                metadata=chunk.metadata.model_dump()
            )
        )
        ids.append(chunk.id)
    vectorstore.add_documents(documents, ids=ids)


def format_context(documents: list[Document]) -> str:
    context_blocks = []

    for index, document in enumerate(documents, start=1):
        content = document.page_content.strip()
        if not content:
            continue

        metadata = document.metadata or {}
        source_parts = []

        if metadata.get("file_name"):
            source_parts.append(f"文件: {metadata['file_name']}")
        if metadata.get("chunk_id"):
            source_parts.append(f"片段: {metadata['chunk_id']}")
        if metadata.get("file_id"):
            source_parts.append(f"文件ID: {metadata['file_id']}")

        source_text = " | ".join(source_parts) if source_parts else "来源未知"
        context_blocks.append(f"[参考片段 {index}]\n{source_text}\n{content}")

    return "\n\n".join(context_blocks)


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

def chat(query: str, file_ids: list[str] | None = None, category_ids: list[str] | None = None, history_messages: list[ChatMessage] | None = None):
    retriever = build_retriever(file_ids, category_ids)
    reranked_results = retriever.invoke(query)
    sources = serialize_documents(reranked_results)
    selected_file_ids = file_ids or []

    if not sources:
        return ChatResponse(
            answer="在提供的文档中没有找到相关信息。",
            sources=[],
            source_count=0,
            selected_file_ids=selected_file_ids,
        )

    context = format_context(reranked_results)
    answer = get_answer(query, context, history_messages)
    return ChatResponse(
        answer=answer,
        sources=sources,
        source_count=len(sources),
        selected_file_ids=selected_file_ids,
    )

def get_chunk(query: str, file_ids: list[str] | None = None, category_ids: list[str] | None = None):
    retriever = build_retriever(file_ids, category_ids)
    retriever_results = retriever.invoke(query)
    return serialize_documents(retriever_results)


def delete_document_assets(file_id: str) -> dict[str, object]:
    record = get_file_record(file_id)
    if not record:
        return {
            "success": False,
            "file_id": file_id,
            "message": "文件不存在或已经删除。",
            "deleted_vector_count": 0,
            "deleted_physical_file": False,
        }

    collection_result = vectorstore._collection.get(
        where={"file_id": file_id},
        include=[],
    )
    document_ids = collection_result.get("ids", [])
    if document_ids:
        vectorstore.delete(ids=document_ids)

    delete_file_record(file_id)

    saved_path = Path(record["saved_path"])
    remaining_records = count_records_by_saved_path(str(saved_path))
    deleted_physical_file = False
    if remaining_records == 0 and saved_path.exists():
        saved_path.unlink()
        deleted_physical_file = True

    return {
        "success": True,
        "file_id": file_id,
        "file_name": record["file_name"],
        "message": "文件记录、向量数据和关联资源已清理。",
        "deleted_vector_count": len(document_ids),
        "deleted_physical_file": deleted_physical_file,
    }

def chat_stream(query: str, file_ids: list[str] | None = None, category_ids: list[str] | None = None, history_messages: list[ChatMessage] | None = None):
    retriever = build_retriever(file_ids, category_ids)
    reranked_results = retriever.invoke(query)
    sources = serialize_documents(reranked_results)
    selected_file_ids = file_ids or []

    if not sources:
        yield {
            "type": "done",
            "answer": "在提供的文档中没有找到相关信息。",
            "sources": [],
            "source_count": 0,
            "selected_file_ids": selected_file_ids,
        }
        return

    context = format_context(reranked_results)

    yield {
    "type": "meta",
    "source_count": len(sources),
    "selected_file_ids": selected_file_ids,
}

    for chunk in stream_answer(query, context, history_messages):
        yield {
            "type": "token",
            "content": chunk,
        }

    yield {
    "type": "done",
    "sources": [item.model_dump() for item in sources],
}