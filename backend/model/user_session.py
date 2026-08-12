from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from model import Base


class UserSession(Base):
    """用户登录会话表，保存访问令牌及其有效期。"""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_expires_at", "expires_at"),
        {"comment": "用户登录会话表，保存认证令牌和过期时间"},
    )

    token: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="访问令牌",
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的用户 ID",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="会话创建时间",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="会话过期时间",
    )
