from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_async import get_current_user_async
from config.database import get_db
from schemas import DeleteDocumentResponse, DocumentInfo, DocumentUpdateRequest
from services.documents import (
    create_document_record,
    delete_document_record,
    get_document_for_user,
    list_documents_by_knowledge_base,
    update_document_record,
)


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/knowledge-bases/{knowledge_base_id}/add",
    response_model=DocumentInfo,
)
async def upload_document_api(
    knowledge_base_id: str,
    file: UploadFile = File(...),
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    document = await create_document_record(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
        file=file,
    )
    return DocumentInfo.model_validate(document)


@router.get(
    "/knowledge-bases/{knowledge_base_id}/documents",
    response_model=list[DocumentInfo],
)
async def list_documents_api(
    knowledge_base_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    documents = await list_documents_by_knowledge_base(
        db=db,
        user_id=current_user.user_id,
        knowledge_base_id=knowledge_base_id,
    )
    return [DocumentInfo.model_validate(document) for document in documents]


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document_api(
    document_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document_for_user(
        db=db,
        user_id=current_user.user_id,
        document_id=document_id,
    )
    return DocumentInfo.model_validate(document)


@router.get("/{document_id}/download")
async def download_document_api(
    document_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document_for_user(
        db=db,
        user_id=current_user.user_id,
        document_id=document_id,
    )
    saved_path = Path(document.saved_path)
    if not saved_path.exists():
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="文档文件不存在")

    return FileResponse(saved_path, filename=document.original_file_name or document.title)


@router.put("/update/{document_id}", response_model=DocumentInfo)
async def update_document_api(
    document_id: str,
    request: DocumentUpdateRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document_for_user(
        db=db,
        user_id=current_user.user_id,
        document_id=document_id,
    )
    updated_document = await update_document_record(
        db=db,
        document=document,
        title=request.title,
        summary=request.summary,
        status=request.status,
    )
    return DocumentInfo.model_validate(updated_document)


@router.delete("/remove/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document_api(
    document_id: str,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    document = await get_document_for_user(
        db=db,
        user_id=current_user.user_id,
        document_id=document_id,
    )
    result = await delete_document_record(db=db, document=document)
    return DeleteDocumentResponse(**result)
