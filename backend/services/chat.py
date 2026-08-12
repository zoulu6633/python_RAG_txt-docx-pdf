from __future__ import annotations

import json
import re

from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crud.chat_server import (
    delete_session,
    get_or_create_session,
    list_recent_messages,
    list_user_sessions,
    rename_session,
    save_message,
    update_session_title,
)
from schemas import ChatMessage, ChatMessageInfo, ChatRequest, ChatResponse, SessionInfo
from services.knowledge_bases import get_knowledge_base_for_user
from services.llm import get_answer, stream_answer
from services.retriever import format_context, retrieve_documents, serialize_sources


async def chat(
    db: AsyncSession,
    request: ChatRequest,
    user_id: str,
    knowledge_base_id: str,
) -> ChatResponse:
    # 权限校验
    await get_knowledge_base_for_user(db, user_id, knowledge_base_id)

    # 获取/创建会话
    session, is_new = await get_or_create_session(
        db, request.session_id, knowledge_base_id, user_id,
    )

    # 加载历史消息
    stored_messages = await list_recent_messages(db, session.session_id, limit=10)
    history = [
        ChatMessage(role=m.role, content=m.content)
        for m in stored_messages
    ]

    # 保存用户消息
    await save_message(db, session.session_id, "user", request.query)

    # 自动更新标题为第一句问题（在检索前执行，确保无论有无结果都更新）
    if is_new and request.query:
        first_sentence = re.split(r'[？。！\n]', request.query.strip())[0]
        title = first_sentence[:80] if first_sentence else request.query[:50]
        await update_session_title(db, session.session_id, title)

    # 检索
    documents = retrieve_documents(
        query=request.query,
        knowledge_base_id=knowledge_base_id,
        history_messages=history,
    )

    if not documents:
        fallback = "在提供的文档中没有找到相关信息。"
        await save_message(db, session.session_id, "assistant", fallback)
        return ChatResponse(
            answer=fallback,
            sources=[],
            session_id=session.session_id,
            source_count=0,
        )

    context = format_context(documents)
    sources = serialize_sources(documents)

    # 生成回答
    try:
        answer = get_answer(request.query, context, history)
        if not answer:
            answer = "在提供的文档中没有找到相关信息。"
    except Exception:
        await save_message(db, session.session_id, "assistant", "请求失败，请检查模型配置或稍后重试。")
        raise

    await save_message(db, session.session_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=session.session_id,
        source_count=len(sources),
    )


async def list_sessions(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
) -> list[SessionInfo]:
    """获取用户在该知识库下的所有会话列表。"""
    from services.knowledge_bases import get_knowledge_base_for_user
    await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    sessions = await list_user_sessions(db, user_id, knowledge_base_id)
    return [
        SessionInfo(
            session_id=s.session_id,
            title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in sessions
    ]


async def get_session_messages(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    knowledge_base_id: str,
) -> list[ChatMessageInfo]:
    """获取指定会话的所有消息。"""
    from services.knowledge_bases import get_knowledge_base_for_user
    await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    messages = await list_recent_messages(db, session_id, limit=100)
    return [
        ChatMessageInfo(
            message_id=m.message_id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


async def delete_session_service(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    knowledge_base_id: str,
) -> bool:
    """删除指定会话（校验会话所属用户）。"""
    from services.knowledge_bases import get_knowledge_base_for_user
    await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    return await delete_session(db, session_id)


async def rename_session_service(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    knowledge_base_id: str,
    title: str,
) -> bool:
    """重命名会话（校验会话所属用户）。"""
    from services.knowledge_bases import get_knowledge_base_for_user
    await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    result = await rename_session(db, session_id, title)
    return result is not None


def _sse_event(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def chat_stream(
    db: AsyncSession,
    request: ChatRequest,
    user_id: str,
    knowledge_base_id: str,
) -> StreamingResponse:
    """流式对话：返回 SSE StreamingResponse，先发 metadata，再逐 token 发 answer。"""
    # 权限校验
    await get_knowledge_base_for_user(db, user_id, knowledge_base_id)

    # 获取/创建会话
    session, is_new = await get_or_create_session(
        db, request.session_id, knowledge_base_id, user_id,
    )

    # 加载历史消息
    stored_messages = await list_recent_messages(db, session.session_id, limit=10)
    history = [
        ChatMessage(role=m.role, content=m.content)
        for m in stored_messages
    ]

    # 保存用户消息
    await save_message(db, session.session_id, "user", request.query)

    # 自动更新标题为第一句问题（在检索前执行，确保无论有无结果都更新）
    if is_new and request.query:
        first_sentence = re.split(r'[？。！\n]', request.query.strip())[0]
        title = first_sentence[:80] if first_sentence else request.query[:50]
        await update_session_title(db, session.session_id, title)

    # 检索
    documents = retrieve_documents(
        query=request.query,
        knowledge_base_id=knowledge_base_id,
        history_messages=history,
    )

    # 无检索结果 → 直接返回 fallback
    if not documents:
        fallback = "在提供的文档中没有找到相关信息。"
        await save_message(db, session.session_id, "assistant", fallback)

        async def _fallback():
            yield _sse_event("metadata", {"session_id": session.session_id, "sources": [], "source_count": 0})
            yield f"event: token\ndata: {fallback}\n\n"
            yield _sse_event("done", "[DONE]")

        return StreamingResponse(_fallback(), media_type="text/event-stream")

    context = format_context(documents)
    sources = serialize_sources(documents)

    async def _generate():
        # 1. 先发元数据
        yield _sse_event("metadata", {
            "session_id": session.session_id,
            "sources": [s.model_dump() for s in sources],
            "source_count": len(sources),
        })

        # 2. 流式输出 token
        full_answer = ""
        try:
            for chunk in stream_answer(request.query, context, history):
                if not chunk:
                    continue
                full_answer += chunk
                yield f"event: token\ndata: {chunk}\n\n"
        except Exception:
            full_answer = "请求失败，请检查模型配置或稍后重试。"
            yield f"event: token\ndata: {full_answer}\n\n"

        # 3. 保存完整回答
        await save_message(db, session.session_id, "assistant", full_answer or "在提供的文档中没有找到相关信息。")
        yield _sse_event("done", "[DONE]")

    return StreamingResponse(_generate(), media_type="text/event-stream")



