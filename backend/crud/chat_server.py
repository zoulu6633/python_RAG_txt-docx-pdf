from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from model import ChatMessage, ChatSession

async def get_or_create_session(
    db: AsyncSession,
    session_id: str | None,
    knowledge_base_id: str,
    user_id: str,
) -> tuple[ChatSession, bool]:
    """获取已有会话或创建新会话。返回 (session, is_new)。"""
    if session_id:
        session = await db.scalar(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        if session:
            return session, False

    session = ChatSession(
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        title="新对话",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session, True


async def save_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    sources: dict | None = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        sources=sources,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def list_recent_messages(
    db: AsyncSession,
    session_id: str,
    limit: int = 10,
) -> list[ChatMessage]:
    result = await db.scalars(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    all_messages = list(result.all())
    return all_messages[-limit:] if len(all_messages) > limit else all_messages


async def list_user_sessions(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
    limit: int = 20,
) -> list[ChatSession]:
    result = await db.scalars(
        select(ChatSession)
        .where(
            ChatSession.user_id == user_id,
            ChatSession.knowledge_base_id == knowledge_base_id,
        )
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
    )
    return list(result.all())


async def update_session_title(
    db: AsyncSession,
    session_id: str,
    title: str,
) -> ChatSession:
    session = await db.scalar(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    if session:
        session.title = title
        await db.commit()
        await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    result = await db.execute(
        delete(ChatSession).where(ChatSession.session_id == session_id)
    )
    await db.commit()
    return result.rowcount > 0


async def rename_session(db: AsyncSession, session_id: str, title: str) -> ChatSession | None:
    session = await db.scalar(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    if session:
        session.title = title
        await db.commit()
        await db.refresh(session)
    return session
