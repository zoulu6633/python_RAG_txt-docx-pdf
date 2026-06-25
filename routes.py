from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
import json
from pathlib import Path
import shutil
from file_store import generate_file_id, get_file_record, init_file_db, list_file_records, save_file_record, list_chat_sessions, list_recent_chat_messages, save_chat_message
from models import ChatResponse, FileRecord, QueryRequest, SourceChunk
from services import add_documents, chat, delete_document_assets, get_chunk, chat_stream

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
FRONTEND_FILE = STATIC_DIR / "index.html"
LIBRARY_FRONTEND_FILE = STATIC_DIR / "library.html"
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
init_file_db()

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
    
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), category_id: str = "student", category_name: str = "学习"):
    original_file_name = Path(file.filename).name
    ext = Path(original_file_name).suffix.lower()
    if ext not in [".txt", ".pdf", ".docx"]:
        return {"error": "不支持的文件类型"}

    file_id = generate_file_id()
    saved_path = UPLOAD_DIR / f"{file_id}_{original_file_name}"

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    add_documents(
        file_path=str(saved_path),
        file_id=file_id,
        user_id="u123",
        file_name=original_file_name,
        category_id=category_id,
        category_name=category_name
    )
    save_file_record(
        file_id=file_id,
        file_name=original_file_name,
        saved_path=str(saved_path),
        user_id="u123",
        category_id=category_id,
        category_name=category_name
    )

    return {
        "file_id": file_id,
        "file_name": original_file_name,
        "path": str(saved_path)
    }


@router.get("/files", response_model=list[FileRecord])
async def get_files(user_id: str | None = None):
    return list_file_records(user_id)


@router.get("/files/{file_id}/view")
async def view_file(file_id: str):
    file_record = get_file_record(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="file_id not found")

    saved_path = Path(file_record["saved_path"])
    if not saved_path.exists():
        raise HTTPException(status_code=404, detail="file not found")

    return FileResponse(saved_path, filename=file_record["file_name"])


@router.delete("/files/{file_id}")
async def delete_file_api(file_id: str):
    result = delete_document_assets(file_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@router.post("/chat", response_model=ChatResponse)
async def chat_api(request: QueryRequest):
    return chat(request.query, request.session_id, request.user_id, request.file_ids, request.category_ids)

@router.post("/get_chunk", response_model=list[SourceChunk])
async def get_chunk_api(request: QueryRequest):
    return get_chunk(request.query, request.file_ids, request.category_ids)

@router.post("/chat/stream")
async def chat_stream_api(request: QueryRequest):
    def event_generator():
        for event in chat_stream(request.query, request.session_id, request.user_id, request.file_ids, request.category_ids):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.get("/chat/sessions")
async def get_chat_sessions(user_id: str):
    return list_chat_sessions(user_id)

@router.get("/chat/sessions/{session_id}/{user_id}/messages")
async def get_chat_session_messages(session_id: str, user_id: str, limit: int = 10):
    sessions=list_chat_sessions(user_id)
    session_ids = [s["session_id"] for s in sessions]
    if session_id not in session_ids:
        raise HTTPException(status_code=404, detail="session_id not found")
    return list_recent_chat_messages(session_id, limit)

