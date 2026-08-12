from __future__ import annotations

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class SourceInfo(BaseModel):
    document_id: str
    title: str
    chunk_id: str
    knowledge_base_name: str
    score: float
    content: str


class ChatRequest(BaseModel):
    query: str
    session_id: str | None = None


class SessionInfo(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str


class ChatMessageInfo(BaseModel):
    message_id: str
    role: str
    content: str
    sources: dict | None = None
    created_at: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
    session_id: str
    source_count: int



