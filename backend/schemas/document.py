from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    knowledge_base_id: str
    created_by: str
    title: str
    original_file_name: str | None
    source_type: str
    content_type: str | None
    file_ext: str | None
    file_size: int | None
    language: str | None
    status: str
    summary: str | None
    error_message: str | None
    chunk_count: int
    token_count: int | None
    last_indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DocumentUpdateRequest(BaseModel):
    title: str | None = None
    summary: str | None = None
    status: str | None = None


class DeleteDocumentResponse(BaseModel):
    message: str
    document_id: str
    deleted_vector_count: int
    deleted_physical_file: bool
