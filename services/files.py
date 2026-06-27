from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path
from file_store import count_records_by_saved_path, delete_file_record, get_file_record, save_chat_message, list_recent_chat_messages, ensure_chat_session, list_chat_sessions, delete_chat_messages    
from models import  ChunkRecord, ChunkMetadata


BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5"
)

vectorstore = Chroma(
    persist_directory=str(CHROMA_DIR),
    embedding_function=embeddings,
    collection_name="documents"
)

CHUNK_SIZE = 300
CHUNK_OVERLAP = 80

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=0
)

# 强制添加重叠
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

# 获取加载器
def get_loader(file_path: str):
    if file_path.endswith(".txt"):
        return TextLoader(file_path, encoding="utf-8")
    elif file_path.endswith(".pdf"):
        return PyPDFLoader(file_path)
    elif file_path.endswith(".docx"):
        return Docx2txtLoader(file_path)
    else:
        raise ValueError("不支持的文件类型")

# 添加文档到向量数据库
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


# 删除文档资产
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

