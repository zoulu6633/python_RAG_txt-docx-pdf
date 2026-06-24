from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    file_id: str
    file_name: str
    chunk_id: str
    user_id: str
    category_id: str
    category_name: str

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChunkRecord(BaseModel):
    id: str
    document: str
    metadata: ChunkMetadata


class QueryRequest(BaseModel):
    query: str
    session_id: str
    user_id: str
    file_ids: list[str] | None = None
    category_ids: list[str] | None = None


class FileRecord(BaseModel):
    file_id: str
    file_name: str
    saved_path: str
    user_id: str
    created_at: str
    category_id: str
    category_name: str



class SourceChunk(BaseModel):
    file_id: str
    file_name: str
    chunk_id: str
    user_id: str
    content: str


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    user_id: str
    sources: list[SourceChunk]
    source_count: int
    selected_file_ids: list[str]

