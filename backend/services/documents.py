from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config import UPLOAD_DIR
from crud.user_server import get_user_by_id
from model import Document
from crud.document_embedding import add_document_chunks
from crud.document_server import (
    create_document_record as create_document_db,
    delete_document_record as delete_document_db,
    get_document_by_id,
    list_documents_by_kb,
    update_document_fields,
)
from services.vector_store import vectorstore
from services.knowledge_bases import get_knowledge_base_for_user


ALLOWED_DOCUMENT_EXTENSIONS = {".txt", ".pdf", ".docx"}


async def list_documents_by_knowledge_base(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
) -> list[Document]:
    await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    return await list_documents_by_kb(db, knowledge_base_id)


async def get_document_for_user(
    db: AsyncSession,
    user_id: str,
    document_id: str,
) -> Document:
    document = await get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    await get_knowledge_base_for_user(db, user_id, document.knowledge_base_id)
    return document


async def create_document_record(
    db: AsyncSession,
    user_id: str,
    knowledge_base_id: str,
    file: UploadFile,
) -> Document:
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    knowledge_base, membership = await get_knowledge_base_for_user(db, user_id, knowledge_base_id)
    if membership not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="无权上传文档")

    original_file_name = Path(file.filename or "document").name
    file_ext = Path(original_file_name).suffix.lower()
    if file_ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    file_bytes = await file.read()
    document_id = f"doc_{uuid4().hex[:12]}"
    saved_path = UPLOAD_DIR / f"{document_id}_{original_file_name}"
    saved_path.write_bytes(file_bytes)

    document = Document(
        document_id=document_id,
        knowledge_base_id=knowledge_base_id,
        created_by=user.user_id,
        title=Path(original_file_name).stem or original_file_name,
        original_file_name=original_file_name,
        saved_path=str(saved_path),
        source_type="upload",
        content_type=file.content_type,
        file_ext=file_ext or None,
        file_size=len(file_bytes),
        status="uploaded",
    )

    try:
        chunk_count = add_document_chunks(
            source_path=str(saved_path),
            document_id=document.document_id,
            user_id=user_id,
            document_name=original_file_name,
            knowledge_base_id=knowledge_base.knowledge_base_id,
            knowledge_base_name=knowledge_base.name,
        )
        document.chunk_count = chunk_count
        document.status = "ready"
        document.error_message = None
        document.last_indexed_at = datetime.now()
    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)

    return await create_document_db(db, document)


async def update_document_record(
    db: AsyncSession,
    document: Document,
    title: str | None = None,
    summary: str | None = None,
    status: str | None = None,
) -> Document:
    if title is not None:
        next_title = title.strip()
        if not next_title:
            raise HTTPException(status_code=400, detail="标题不能为空")
        document.title = next_title

    if summary is not None:
        document.summary = summary.strip() or None

    if status is not None:
        next_status = status.strip()
        if not next_status:
            raise HTTPException(status_code=400, detail="状态不能为空")
        document.status = next_status

    return await update_document_fields(db, document)


async def delete_document_record(
    db: AsyncSession,
    document: Document,
) -> dict[str, object]:
    collection_result = vectorstore._collection.get(
        where={"document_id": document.document_id},
        include=[],
    )
    document_ids = collection_result.get("ids", [])
    if document_ids:
        vectorstore.delete(ids=document_ids)

    saved_path = Path(document.saved_path)
    deleted_physical_file = False
    if saved_path.exists():
        saved_path.unlink()
        deleted_physical_file = True

    await delete_document_db(db, document)

    return {
        "message": "文档记录、向量数据和物理文件已删除",
        "document_id": document.document_id,
        "deleted_vector_count": len(document_ids),
        "deleted_physical_file": deleted_physical_file,
    }
