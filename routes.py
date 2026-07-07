from fastapi import APIRouter, Depends, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
import json
from pathlib import Path
import shutil
from auth import create_access_token, get_current_user, login_user, logout_user, register_user
from file_store import generate_file_id, get_file_record, list_file_records, save_file_record, list_chat_sessions, list_recent_chat_messages
from models import ChatResponse, FileRecord, LoginRequest, MessageResponse, QueryRequest, RegisterRequest, SourceChunk, TokenResponse, UserInfo
from services.chat import chat, chat_stream
from services.files import add_documents, delete_document_assets
from services.retriever import  get_chunk
from app_init import UPLOAD_DIR, FRONTEND_FILE, LIBRARY_FRONTEND_FILE, AUTH_FRONTEND_FILE

router = APIRouter()



@router.get("/")
async def root():
    if FRONTEND_FILE.exists():
        return FileResponse(FRONTEND_FILE)
    return {"message": "RAG frontend is not ready yet."}

@router.get("/library")
async def library_page():
    if LIBRARY_FRONTEND_FILE.exists():
        return FileResponse(LIBRARY_FRONTEND_FILE)
    return {"message": "RAG library frontend is not ready yet."}


@router.get("/login")
async def login_page():
    if AUTH_FRONTEND_FILE.exists():
        return FileResponse(AUTH_FRONTEND_FILE)
    return {"message": "RAG auth frontend is not ready yet."}


@router.post("/auth/register", response_model=TokenResponse)
async def register_api(request: RegisterRequest):
    user = register_user(request.username, request.password)
    access_token, expires_at = create_access_token(user["user_id"])
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserInfo(**user),
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login_api(request: LoginRequest):
    user, access_token, expires_at = login_user(request.username, request.password)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserInfo(**user),
    )


@router.get("/auth/me", response_model=UserInfo)
async def me_api(current_user: dict[str, str] = Depends(get_current_user)):
    return UserInfo(**current_user)


@router.post("/auth/logout", response_model=MessageResponse)
async def logout_api(result: dict[str, str] = Depends(logout_user)):
    return MessageResponse(**result)
    
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category_id: str = "student",
    category_name: str = "学习",
    current_user: dict[str, str] = Depends(get_current_user),
):
    original_file_name = Path(file.filename).name
    ext = Path(original_file_name).suffix.lower()
    if ext not in [".txt", ".pdf", ".docx"]:
        return {"error": "不支持的文件类型"}

    file_id = generate_file_id()
    user_id = current_user["user_id"]
    saved_path = UPLOAD_DIR / f"{file_id}_{original_file_name}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    add_documents(
        file_path=str(saved_path),
        file_id=file_id,
        user_id=user_id,
        file_name=original_file_name,
        category_id=category_id,
        category_name=category_name
    )
    save_file_record(
        file_id=file_id,
        file_name=original_file_name,
        saved_path=str(saved_path),
        user_id=user_id,
        category_id=category_id,
        category_name=category_name
    )

    return {
        "file_id": file_id,
        "file_name": original_file_name,
        "path": str(saved_path)
    }


@router.get("/files", response_model=list[FileRecord])
async def get_files(current_user: dict[str, str] = Depends(get_current_user)):
    return list_file_records(current_user["user_id"])


@router.get("/files/{file_id}/view")
async def view_file(file_id: str, current_user: dict[str, str] = Depends(get_current_user)):
    file_record = get_file_record(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="file_id not found")
    if file_record["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="file_id not found")

    saved_path = Path(file_record["saved_path"])
    if not saved_path.exists():
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(saved_path, filename=file_record["file_name"])


@router.delete("/files/{file_id}")
async def delete_file_api(file_id: str, current_user: dict[str, str] = Depends(get_current_user)):
    file_record = get_file_record(file_id)
    if not file_record or file_record["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=404, detail="file_id not found")
    result = delete_document_assets(file_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@router.post("/chat", response_model=ChatResponse)
async def chat_api(request: QueryRequest, current_user: dict[str, str] = Depends(get_current_user)):
    return chat(request.query, request.session_id, current_user["user_id"], request.file_ids, request.category_ids)

@router.post("/get_chunk", response_model=list[SourceChunk])
async def get_chunk_api(request: QueryRequest, current_user: dict[str, str] = Depends(get_current_user)):
    return get_chunk(request.query, current_user["user_id"], request.file_ids, request.category_ids)

@router.post("/chat/stream")
async def chat_stream_api(request: QueryRequest, current_user: dict[str, str] = Depends(get_current_user)):
    def event_generator():
        for event in chat_stream(request.query, request.session_id, current_user["user_id"], request.file_ids, request.category_ids):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.get("/chat/sessions")
async def get_chat_sessions(current_user: dict[str, str] = Depends(get_current_user)):
    return list_chat_sessions(current_user["user_id"])

@router.get("/chat/sessions/{session_id}/messages")
async def get_chat_session_messages(
    session_id: str,
    limit: int = 10,
    current_user: dict[str, str] = Depends(get_current_user),
):
    sessions = list_chat_sessions(current_user["user_id"])
    session_ids = [s["session_id"] for s in sessions]
    if session_id not in session_ids:
        raise HTTPException(status_code=404, detail="session_id not found")
    return list_recent_chat_messages(session_id, limit)

