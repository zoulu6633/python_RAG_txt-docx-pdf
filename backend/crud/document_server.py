from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from model import Document


async def get_document_by_id(
    db: AsyncSession,
    document_id: str,
) -> Document | None:
    return await db.scalar(
        select(Document).where(Document.document_id == document_id)
    )


async def list_documents_by_kb(
    db: AsyncSession,
    knowledge_base_id: str,
) -> list[Document]:
    result = await db.scalars(
        select(Document)
        .where(Document.knowledge_base_id == knowledge_base_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.all())


async def create_document_record(
    db: AsyncSession,
    document: Document,
) -> Document:
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def update_document_fields(
    db: AsyncSession,
    document: Document,
) -> Document:
    await db.commit()
    await db.refresh(document)
    return document


async def delete_document_record(
    db: AsyncSession,
    document: Document,
) -> None:
    await db.delete(document)
    await db.commit()
