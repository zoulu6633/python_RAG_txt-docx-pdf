from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_async import get_current_user_async
from config.database import get_db
from schemas import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseInfo,
    KnowledgeBaseMemberInfo,
    KnowledgeBaseMemberUpdateRequest,
    KnowledgeBaseUpdateRequest,
)
from services.knowledge_bases import (
    add_knowledge_base_member,
    create_knowledge_base,
    delete_knowledge_base,
    ensure_can_manage_knowledge_base,
    ensure_is_owner,
    get_knowledge_base_for_user,
    get_member_for_management,
    list_knowledge_base_members,
    list_knowledge_bases,
    remove_knowledge_base_member,
    update_knowledge_base,
    update_knowledge_base_member,
)


router = APIRouter(prefix="/knowledge/bases", tags=["knowledge_bases"])


def _build_member_info(member, user) -> KnowledgeBaseMemberInfo:
    return KnowledgeBaseMemberInfo(
        knowledge_base_member_id=member.knowledge_base_member_id,
        knowledge_base_id=member.knowledge_base_id,
        user_id=member.user_id,
        username=user.username,
        display_name=user.display_name,
        role=member.role,
        status=member.status,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


@router.post("/create", response_model=KnowledgeBaseInfo)
async def create_knowledge_base_api(
    request: KnowledgeBaseCreateRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    knowledge_base = await create_knowledge_base(
        db=db,
        user_id=current_user.user_id,
        request=request,
    )
    return KnowledgeBaseInfo.model_validate(knowledge_base)


@router.get("/list", response_model=list[KnowledgeBaseInfo])
async def list_knowledge_bases_api(
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    knowledge_bases = await list_knowledge_bases(db=db, user_id=current_user.user_id)
    return [KnowledgeBaseInfo.model_validate(item) for item in knowledge_bases]


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseInfo)
async def get_knowledge_base_api(
    knowledge_base_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    knowledge_base, _ = await get_knowledge_base_for_user(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    return KnowledgeBaseInfo.model_validate(knowledge_base)


@router.put("/update/{knowledge_base_id}", response_model=KnowledgeBaseInfo)
async def update_knowledge_base_api(
    knowledge_base_id: str,
    request: KnowledgeBaseUpdateRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    knowledge_base, _ = await ensure_can_manage_knowledge_base(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    updated = await update_knowledge_base(
        db=db,
        knowledge_base=knowledge_base,
        request=request,
    )
    return KnowledgeBaseInfo.model_validate(updated)


@router.delete("/delete/{knowledge_base_id}")
async def delete_knowledge_base_api(
    knowledge_base_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    knowledge_base = await ensure_is_owner(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    await delete_knowledge_base(db=db, knowledge_base=knowledge_base)
    return {"message": "知识库已删除", "knowledge_base_id": knowledge_base_id}


@router.get(
    "/knowledge-bases/{knowledge_base_id}/members",
    response_model=list[KnowledgeBaseMemberInfo],
)
async def list_knowledge_base_members_api(
    knowledge_base_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    await get_knowledge_base_for_user(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    rows = await list_knowledge_base_members(db=db, knowledge_base_id=knowledge_base_id)
    return [_build_member_info(member, user) for member, user in rows]


@router.post(
    "/knowledge-bases/{knowledge_base_id}/members",
    response_model=KnowledgeBaseMemberInfo,
)
async def add_knowledge_base_member_api(
    knowledge_base_id: str,
    member_name: str,
    role: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    await ensure_can_manage_knowledge_base(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    member, user = await add_knowledge_base_member(
        db=db,
        knowledge_base_id=knowledge_base_id,
        member_name=member_name,
        role=role,
    )
    return _build_member_info(member, user)


@router.put(
    "/knowledge-bases/{knowledge_base_id}/members/{knowledge_base_member_id}",
    response_model=KnowledgeBaseMemberInfo,
)
async def update_knowledge_base_member_api(
    knowledge_base_id: str,
    knowledge_base_member_id: str,
    request: KnowledgeBaseMemberUpdateRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    await ensure_can_manage_knowledge_base(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    member, user = await get_member_for_management(
        db=db,
        knowledge_base_id=knowledge_base_id,
        knowledge_base_member_id=knowledge_base_member_id,
    )
    updated_member = await update_knowledge_base_member(
        db=db,
        member=member,
        role=request.role,
        status=request.status,
    )
    return _build_member_info(updated_member, user)


@router.delete("/knowledge-bases/{knowledge_base_id}/members/{knowledge_base_member_id}")
async def remove_knowledge_base_member_api(
    knowledge_base_id: str,
    knowledge_base_member_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    await ensure_can_manage_knowledge_base(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    member, _ = await get_member_for_management(
        db=db,
        knowledge_base_id=knowledge_base_id,
        knowledge_base_member_id=knowledge_base_member_id,
    )
    await remove_knowledge_base_member(db=db, member=member)
    return {"message": "成员已移除", "knowledge_base_member_id": knowledge_base_member_id}
