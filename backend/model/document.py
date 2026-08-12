from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model import Base, TimestampMixin

if TYPE_CHECKING:
    from model.knowledge_base import KnowledgeBase
    from model.user import User


class Document(Base, TimestampMixin):
    """文档表，记录知识库中文档的元信息、处理状态和索引统计信息。"""

    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_kb_status", "knowledge_base_id", "status"),
        Index("idx_documents_creator_status", "created_by", "status"),
        {"comment": "知识库文档表，保存文档元信息、处理状态和索引统计"},
    )

    document_id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: f"doc_{uuid4().hex[:12]}",
        comment="文档主键 ID",
    )
    knowledge_base_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="CASCADE"),
        nullable=False,
        comment="所属知识库 ID",
    )
    created_by: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="文档创建者用户 ID",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="文档标题",
    )
    original_file_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="用户上传时的原始文件名",
    )
    saved_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="文档在存储介质中的保存路径",
    )
    source_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="upload",
        comment="文档来源类型，如 upload、url、manual",
    )
    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="文档 MIME 类型",
    )
    file_ext: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="文档文件扩展名",
    )
    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="文档文件大小，单位字节",
    )
    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="文档内容语言",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="uploaded",
        comment="文档处理状态",
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="文档摘要",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="文档处理失败时的错误信息",
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="文档切分后的块数量",
    )
    token_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="文档总 token 数",
    )
    last_indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最近一次完成索引的时间",
    )

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
    creator: Mapped["User"] = relationship(back_populates="documents")
