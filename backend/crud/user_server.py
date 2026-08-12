from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from model import User, UserSession


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    username: str,
    password_hash: str,
    display_name: str | None = None,
) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        display_name=display_name,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    username: str | None = None,
    display_name: str | None = None,
    password_hash: str | None = None,
    last_login_at: datetime | None = None,
) -> User:
    if username is not None:
        user.username = username
    if display_name is not None:
        user.display_name = display_name
    if password_hash is not None:
        user.password_hash = password_hash
    if last_login_at is not None:
        user.last_login_at = last_login_at
    await db.commit()
    await db.refresh(user)
    return user


async def create_user_session(
    db: AsyncSession,
    token: str,
    user_id: str,
    created_at: datetime,
    expires_at: datetime,
) -> UserSession:
    session = UserSession(
        token=token,
        user_id=user_id,
        created_at=created_at,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    return session


async def delete_user_session(db: AsyncSession, token: str) -> int:
    result = await db.execute(delete(UserSession).where(UserSession.token == token))
    await db.commit()
    return int(result.rowcount or 0)


async def delete_expired_user_sessions(db: AsyncSession, now: datetime) -> int:
    result = await db.execute(delete(UserSession).where(UserSession.expires_at <= now))
    await db.commit()
    return int(result.rowcount or 0)


async def get_user_by_session_token(
    db: AsyncSession,
    token: str,
    now: datetime,
) -> User | None:
    result = await db.execute(
        select(User)
        .join(UserSession, User.user_id == UserSession.user_id)
        .where(
            UserSession.token == token,
            UserSession.expires_at > now,
        )
    )
    return result.scalar_one_or_none()
