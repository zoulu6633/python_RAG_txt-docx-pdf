from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KnowledgeBaseCreateRequest(BaseModel):
    name: str
    description: str | None = None
    visibility: str = "private"


class KnowledgeBaseUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None
    status: str | None = None


class KnowledgeBaseInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    knowledge_base_id: str
    owner_id: str
    name: str
    description: str | None
    visibility: str
    status: str
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseMemberUpdateRequest(BaseModel):
    role: str | None = None
    status: str | None = None


class KnowledgeBaseMemberInfo(BaseModel):
    knowledge_base_member_id: str
    knowledge_base_id: str
    user_id: str
    username: str
    display_name: str | None
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
