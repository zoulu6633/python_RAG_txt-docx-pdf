from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model import Base, TimestampMixin


class ChatSession(Base, TimestampMixin):
    """对话会话表，记录用户与知识库之间的对话。"""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        Index("idx_chat_sessions_user", "user_id"),
        Index("idx_chat_sessions_kb", "knowledge_base_id"),
        {"comment": "对话会话表"},
    )

    session_id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: f"chat_{uuid4().hex[:12]}",
        comment="会话主键 ID",
    )
    knowledge_base_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联知识库 ID",
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="创建者用户 ID",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="新对话",
        comment="会话标题",
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        order_by="ChatMessage.created_at.asc()",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    """对话消息表，记录会话中的每一条消息。"""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_chat_messages_session", "session_id"),
        {"comment": "对话消息表"},
    )

    message_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: f"msg_{uuid4().hex[:12]}",
        comment="消息主键 ID",
    )
    session_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        comment="所属会话 ID",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="消息角色：user / assistant",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容",
    )
    sources: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="assistant 消息的引用来源（JSON）",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        comment="消息创建时间",
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
