from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model import Base, TimestampMixin

if TYPE_CHECKING:
    from model.document import Document
    from model.knowledge_base import KnowledgeBase
    from model.knowledge_base_member import KnowledgeBaseMember


class User(Base, TimestampMixin):
    """用户表，保存账号身份信息，并作为知识库、文档和成员关系的主体。"""

    __tablename__ = "users"
    __table_args__ = {"comment": "系统用户表，保存账号基础信息和用户状态"}

    user_id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: f"user_{uuid4().hex[:12]}",
        comment="用户主键 ID",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="登录用户名，要求唯一",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="密码哈希值，不保存明文密码",
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="用户展示昵称",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="用户是否可用",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="最近一次登录时间",
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="creator",
        cascade="all, delete-orphan",
    )
    owned_knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    knowledge_base_memberships: Mapped[list["KnowledgeBaseMember"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
