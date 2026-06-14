from fastapi import APIRouter, HTTPException
from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
from file_store import generate_file_id, init_file_db, list_file_records, save_file_record
from models import ChatResponse, FileRecord, QueryRequest, SourceChunk
from services import add_documents, chat, delete_document_assets, get_chunk

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
FRONTEND_FILE = STATIC_DIR / "index.html"
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
init_file_db()

@router.get("/")
async def root():
    if FRONTEND_FILE.exists():
        return FileResponse(FRONTEND_FILE)
    return {"message": "RAG frontend is not ready yet."}
    
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


@router.delete("/files/{file_id}")
async def delete_file_api(file_id: str):
    result = delete_document_assets(file_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@router.post("/chat", response_model=ChatResponse)
async def chat_api(request: QueryRequest):
    return chat(request.query, request.file_ids, request.category_ids)

@router.post("/get_chunk", response_model=list[SourceChunk])
async def get_chunk_api(request: QueryRequest):
    return get_chunk(request.query, request.file_ids, request.category_ids)


