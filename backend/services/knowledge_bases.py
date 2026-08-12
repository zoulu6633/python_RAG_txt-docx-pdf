from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from model import KnowledgeBase, KnowledgeBaseMember, User
from crud.knowledge_base_server import (
    create_knowledge_base as create_knowledge_base_record,
    create_knowledge_base_member,
    delete_knowledge_base as delete_knowledge_base_record,
    delete_member,
    get_knowledge_base_by_id,
    get_member_by_user_id,
    get_member_for_management as get_member_for_management_record,
    get_membership,
    list_knowledge_base_members as list_knowledge_base_members_record,
    list_knowledge_bases_for_user,
    save_member,
    update_knowledge_base_record
)
from crud.user_server import get_user_by_id, get_user_by_username
from schemas import KnowledgeBaseCreateRequest, KnowledgeBaseUpdateRequest



MANAGEABLE_MEMBER_ROLES = {"owner", "admin"}


async def _require_user_by_id(db: AsyncSession, user_id: str) -> User:
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


async def _require_user_by_username(db: AsyncSession, username: str) -> User:
    normalized_username = username.strip().lower()
    user = await get_user_by_username(db, normalized_username)
    if user is None:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    return user


async def _get_membership(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
) -> KnowledgeBaseMember | None:
    return await get_membership(db, user_id, knowledge_base_id)


async def get_knowledge_base_for_user(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
) -> tuple[KnowledgeBase, str]:
    knowledge_base = await get_knowledge_base_by_id(db, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    if knowledge_base.owner_id == user_id:
        return knowledge_base, "owner"

    membership = await _get_membership(db, user_id, knowledge_base_id)
    if membership is None:
        raise HTTPException(status_code=403, detail="无权访问该知识库")

    return knowledge_base, membership.role


async def ensure_can_manage_knowledge_base(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
) -> tuple[KnowledgeBase, str]:
    knowledge_base, role = await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    if role not in MANAGEABLE_MEMBER_ROLES:
        raise HTTPException(status_code=403, detail="无权管理该知识库")
    return knowledge_base, role


async def ensure_is_owner(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
) -> KnowledgeBase:
    knowledge_base, role = await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    if role != "owner":
        raise HTTPException(status_code=403, detail="仅知识库拥有者可执行该操作")
    return knowledge_base


async def create_knowledge_base(
    db: AsyncSession,
    user_id: str,
    request: KnowledgeBaseCreateRequest,
) -> KnowledgeBase:
    owner = await _require_user_by_id(db, user_id)

    knowledge_base = await create_knowledge_base_record(
        db=db,
        owner_id=owner.user_id,
        name=request.name.strip(),
        description=request.description.strip() if request.description else None,
        visibility=request.visibility.strip() or "private",
    )

    await create_knowledge_base_member(
        db=db,
        knowledge_base_id=knowledge_base.knowledge_base_id,
        user_id=owner.user_id,
        role="owner",
        status="active",
    )
    return knowledge_base


async def list_knowledge_bases(
    db: AsyncSession,
    user_id: str,
) -> list[KnowledgeBase]:
    await _require_user_by_id(db, user_id)
    list = await list_knowledge_bases_for_user(db, user_id)
    return list


async def update_knowledge_base(
    db: AsyncSession,
    knowledge_base: KnowledgeBase,
    request: KnowledgeBaseUpdateRequest,
) -> KnowledgeBase:
    if request.name is not None:
        next_name = request.name.strip()
        if not next_name:
            raise HTTPException(status_code=400, detail="知识库名称不能为空")
        knowledge_base.name = next_name

    if request.description is not None:
        knowledge_base.description = request.description.strip() or None

    if request.visibility is not None:
        next_visibility = request.visibility.strip()
        if not next_visibility:
            raise HTTPException(status_code=400, detail="可见性不能为空")
        knowledge_base.visibility = next_visibility

    if request.status is not None:
        next_status = request.status.strip()
        if not next_status:
            raise HTTPException(status_code=400, detail="状态不能为空")
        knowledge_base.status = next_status

    return await update_knowledge_base_record(db, knowledge_base)


async def delete_knowledge_base(
    db: AsyncSession,
    knowledge_base: KnowledgeBase,
) -> None:
    await delete_knowledge_base_record(db, knowledge_base)


async def list_knowledge_base_members(
    db: AsyncSession,
    knowledge_base_id: str,
) -> list[tuple[KnowledgeBaseMember, User]]:
    return await list_knowledge_base_members_record(db, knowledge_base_id)


async def add_knowledge_base_member(
    db: AsyncSession,
    knowledge_base_id: str,
    member_name: str,
    role: str = "viewer",
) -> tuple[KnowledgeBaseMember, User]:
    user = await _require_user_by_username(db, member_name) 
    existing_member = await get_member_by_user_id(db, knowledge_base_id, user.user_id)
    if existing_member is not None:
        raise HTTPException(status_code=409, detail="该用户已在知识库成员列表中")

    member = await create_knowledge_base_member(
        db=db,
        knowledge_base_id=knowledge_base_id,
        user_id=user.user_id,
        role=role.strip() or "viewer",
        status="active",
    )
    member = await save_member(db, member)
    return member, user


async def get_member_for_management(
    db: AsyncSession,
    knowledge_base_id: str,
    knowledge_base_member_id: str,
) -> tuple[KnowledgeBaseMember, User]:
    row = await get_member_for_management_record(db, knowledge_base_id, knowledge_base_member_id)
    if row is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    member, user = row
    return member, user


async def update_knowledge_base_member(
    db: AsyncSession,
    member: KnowledgeBaseMember,
    role: str | None = None,
    status: str | None = None,
) -> KnowledgeBaseMember:
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="拥有者角色不能直接修改")

    if role is not None:
        next_role = role.strip()
        if not next_role:
            raise HTTPException(status_code=400, detail="角色不能为空")
        member.role = next_role

    if status is not None:
        next_status = status.strip()
        if not next_status:
            raise HTTPException(status_code=400, detail="状态不能为空")
        member.status = next_status

    return await save_member(db, member)


async def remove_knowledge_base_member(
    db: AsyncSession,
    member: KnowledgeBaseMember,
) -> None:
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="不能移除知识库拥有者")
    await delete_member(db, member)
