from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from pathlib import Path

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

# 加载重排模型
rerank_model = HuggingFaceCrossEncoder(
    model_name="BAAI/bge-reranker-base"
)

# 定义重排器，只保留前 5
compressor = CrossEncoderReranker(
    model=rerank_model,
    top_n=5
)