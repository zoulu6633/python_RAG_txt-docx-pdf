from __future__ import annotations

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from model import KnowledgeBase, KnowledgeBaseMember, User



async def get_knowledge_base_by_id(
    db: AsyncSession,
    knowledge_base_id: str,
) -> KnowledgeBase | None:
    return await db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.knowledge_base_id == knowledge_base_id,
        )
    )


async def list_knowledge_bases_for_user(
    db: AsyncSession,
    user_id: str,
) -> list[KnowledgeBase]:
    result = await db.scalars(
        select(KnowledgeBase)
        .outerjoin(
            KnowledgeBaseMember,
            and_(
                KnowledgeBaseMember.knowledge_base_id == KnowledgeBase.knowledge_base_id,
                KnowledgeBaseMember.user_id == user_id,
                KnowledgeBaseMember.status == "active",
            ),
        )
        .where(
            or_(
                KnowledgeBase.owner_id == user_id,
                KnowledgeBaseMember.knowledge_base_member_id.is_not(None),
            )
        )
        .order_by(KnowledgeBase.created_at.desc())
    )
    return list(result.unique().all())


async def create_knowledge_base(
    db: AsyncSession,
    owner_id: str,
    name: str,
    description: str | None,
    visibility: str,
) -> KnowledgeBase:
    knowledge_base = KnowledgeBase(
        owner_id=owner_id,
        name=name,
        description=description,
        visibility=visibility,
        status="active",
    )
    db.add(knowledge_base)
    await db.commit()
    await db.refresh(knowledge_base)
    return knowledge_base


async def create_knowledge_base_member(
    db: AsyncSession,
    knowledge_base_id: str,
    user_id: str,
    role: str,
    status: str = "active",
) -> KnowledgeBaseMember:
    member = KnowledgeBaseMember(
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        role=role,
        status=status,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def get_membership(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
) -> KnowledgeBaseMember | None:
    return await db.scalar(
        select(KnowledgeBaseMember).where(
            KnowledgeBaseMember.knowledge_base_id == knowledge_base_id,
            KnowledgeBaseMember.user_id == user_id,
            KnowledgeBaseMember.status == "active",
        )
    )


async def list_knowledge_base_members(
    db: AsyncSession,
    knowledge_base_id: str,
) -> list[tuple[KnowledgeBaseMember, User]]:
    result = await db.execute(
        select(KnowledgeBaseMember, User)
        .join(User, User.user_id == KnowledgeBaseMember.user_id)
        .where(KnowledgeBaseMember.knowledge_base_id == knowledge_base_id)
        .order_by(KnowledgeBaseMember.created_at.asc())
    )
    return list(result.all())

async def update_knowledge_base_record(
    db: AsyncSession,
    knowledge_base: KnowledgeBase,
) -> KnowledgeBase:
    await db.execute(
        update(KnowledgeBase).where(
            KnowledgeBase.knowledge_base_id == knowledge_base.knowledge_base_id,
        ).values(
            name=knowledge_base.name,
            description=knowledge_base.description,
            visibility=knowledge_base.visibility,
            status=knowledge_base.status,
        )
    )
    await db.commit()
    await db.refresh(knowledge_base)
    return knowledge_base


async def get_member_for_management(
    db: AsyncSession,
    knowledge_base_id: str,
    knowledge_base_member_id: str,
) -> tuple[KnowledgeBaseMember, User] | None:
    result = await db.execute(
        select(KnowledgeBaseMember, User)
        .join(User, User.user_id == KnowledgeBaseMember.user_id)
        .where(
            KnowledgeBaseMember.knowledge_base_id == knowledge_base_id,
            KnowledgeBaseMember.knowledge_base_member_id == knowledge_base_member_id,
        )
    )
    return result.first()


async def get_member_by_user_id(
    db: AsyncSession,
    knowledge_base_id: str,
    user_id: str,
) -> KnowledgeBaseMember | None:
    return await db.scalar(
        select(KnowledgeBaseMember).where(
            KnowledgeBaseMember.knowledge_base_id == knowledge_base_id,
            KnowledgeBaseMember.user_id == user_id,
        )
    )



async def save_member(db: AsyncSession, member: KnowledgeBaseMember) -> KnowledgeBaseMember:
    await db.commit()
    await db.refresh(member)
    return member


async def delete_knowledge_base(db: AsyncSession, knowledge_base: KnowledgeBase) -> None:
    await db.delete(knowledge_base)
    await db.commit()


async def delete_member(db: AsyncSession, member: KnowledgeBaseMember) -> None:
    await db.delete(member)
    await db.commit()


