from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from schemas import ChatMessageInfo, ChatRequest, ChatResponse, SessionInfo
from services.auth_async import get_current_user_async
from services.chat import chat as chat_service
from services.chat import chat_stream, delete_session_service, get_session_messages, list_sessions, rename_session_service


router = APIRouter(prefix="/knowledge-bases", tags=["chat"])


@router.post("/{knowledge_base_id}/chat", response_model=ChatResponse)
async def chat_api(
    knowledge_base_id: str,
    request: ChatRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service(
        db=db,
        request=request,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )


@router.post("/{knowledge_base_id}/chat/stream")
async def chat_stream_api(
    knowledge_base_id: str,
    request: ChatRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return await chat_stream(
        db=db,
        request=request,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )


@router.get("/{knowledge_base_id}/sessions", response_model=list[SessionInfo])
async def list_sessions_api(
    knowledge_base_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    return await list_sessions(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )


@router.get("/{knowledge_base_id}/sessions/{session_id}/messages", response_model=list[ChatMessageInfo])
async def get_session_messages_api(
    knowledge_base_id: str,
    session_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    return await get_session_messages(
        db=db,
        user_id=current_user.user_id,
        session_id=session_id,
        knowledge_base_id=knowledge_base_id,
    )


@router.delete("/{knowledge_base_id}/sessions/{session_id}")
async def delete_session_api(
    knowledge_base_id: str,
    session_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    ok = await delete_session_service(
        db=db,
        user_id=current_user.user_id,
        session_id=session_id,
        knowledge_base_id=knowledge_base_id,
    )
    return {"success": ok, "message": "会话已删除" if ok else "会话不存在"}


@router.put("/{knowledge_base_id}/sessions/{session_id}/title")
async def rename_session_api(
    knowledge_base_id: str,
    session_id: str,
    body: dict,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    title = body.get("title", "").strip()
    if not title:
        return {"success": False, "message": "标题不能为空"}
    ok = await rename_session_service(
        db=db,
        user_id=current_user.user_id,
        session_id=session_id,
        knowledge_base_id=knowledge_base_id,
        title=title,
    )
    return {"success": ok, "message": "重命名成功" if ok else "会话不存在"}
