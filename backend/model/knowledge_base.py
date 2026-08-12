from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model import Base, TimestampMixin

if TYPE_CHECKING:
    from model.document import Document
    from model.knowledge_base_member import KnowledgeBaseMember
    from model.user import User


class KnowledgeBase(Base, TimestampMixin):
    """知识库表，表示团队或项目级知识空间，是文档和成员权限的归属容器。"""

    __tablename__ = "knowledge_bases"
    __table_args__ = (
        Index("idx_knowledge_bases_owner_status", "owner_id", "status"),
        {"comment": "知识库主表，表示一个团队或项目级知识空间"},
    )

    knowledge_base_id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: f"kb_{uuid4().hex[:12]}",
        comment="知识库主键 ID",
    )
    owner_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="知识库拥有者用户 ID",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="知识库名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="知识库描述信息",
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="private",
        comment="知识库可见性，如 private 或 public",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="知识库状态，如 active 或 archived",
    )

    owner: Mapped["User"] = relationship(back_populates="owned_knowledge_bases")
    members: Mapped[list["KnowledgeBaseMember"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
