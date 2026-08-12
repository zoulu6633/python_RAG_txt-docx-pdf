from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from model import Base, TimestampMixin

if TYPE_CHECKING:
    from model.knowledge_base import KnowledgeBase
    from model.user import User


class KnowledgeBaseMember(Base, TimestampMixin):
    """知识库成员关系表，定义用户在某个知识库中的角色和状态。"""

    __tablename__ = "knowledge_base_members"
    __table_args__ = (
        UniqueConstraint("knowledge_base_id", "user_id", name="uq_kb_member_unique"),
        Index("idx_kb_members_user_role", "user_id", "role"),
        {"comment": "知识库成员关系表，定义用户在知识库中的角色和状态"},
    )

    knowledge_base_member_id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: f"kbm_{uuid4().hex[:12]}",
        comment="知识库成员关系主键 ID",
    )
    knowledge_base_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("knowledge_bases.knowledge_base_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的知识库 ID",
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的用户 ID",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="viewer",
        comment="用户在知识库中的角色",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="成员关系状态",
    )

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="knowledge_base_memberships")
