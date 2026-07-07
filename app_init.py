from pathlib import Path
from file_store import init_file_db

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
FRONTEND_FILE = STATIC_DIR / "index.html"
LIBRARY_FRONTEND_FILE = STATIC_DIR / "library.html"
AUTH_FRONTEND_FILE = STATIC_DIR / "auth.html"


def init_app() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    init_file_db()
