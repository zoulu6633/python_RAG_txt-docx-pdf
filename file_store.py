from __future__ import annotations

import sqlite3
from datetime import datetime, UTC
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"


def _get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_file_db() -> None:
    with _get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                file_id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                saved_path TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                category_id TEXT NOT NULL,
                category_name TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id)
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO app_meta(key, value)
            VALUES ('file_seq', '0')
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session_time
            ON chat_messages(session_id, created_at);
            """
        )
        connection.commit()


def generate_file_id() -> str:
    init_file_db()

    with _get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT value FROM app_meta WHERE key = 'file_seq'"
        ).fetchone()
        next_seq = int(row["value"]) + 1 if row else 1
        connection.execute(
            "UPDATE app_meta SET value = ? WHERE key = 'file_seq'",
            (str(next_seq),),
        )
        connection.commit()

    return f"doc_{next_seq:06d}"


def save_file_record(
    file_id: str,
    file_name: str,
    saved_path: str,
    user_id: str,
    category_id: str,
    category_name: str,
) -> None:
    init_file_db()
    created_at = datetime.now(UTC).isoformat()

    with _get_connection() as connection:
        connection.execute(
            """
            INSERT INTO files(file_id, file_name, saved_path, user_id, created_at, category_id, category_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (file_id, file_name, saved_path, user_id, created_at, category_id, category_name),
        )
        connection.commit()


def list_file_records(user_id: str | None = None) -> list[dict[str, str]]:
    init_file_db()

    query = """
        SELECT file_id, file_name, saved_path, user_id, created_at, category_id, category_name
        FROM files
    """
    params: tuple[str, ...] = ()

    if user_id:
        query += " WHERE user_id = ?"
        params = (user_id,)

    query += " ORDER BY created_at DESC"

    with _get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def get_file_record(file_id: str) -> dict[str, str] | None:
    init_file_db()

    with _get_connection() as connection:
        row = connection.execute(
            """
            SELECT file_id, file_name, saved_path, user_id, created_at, category_id, category_name
            FROM files
            WHERE file_id = ?
            """,
            (file_id,),
        ).fetchone()

    return dict(row) if row else None


def count_records_by_saved_path(saved_path: str) -> int:
    init_file_db()

    with _get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM files WHERE saved_path = ?",
            (saved_path,),
        ).fetchone()

    return int(row["total"]) if row else 0


def delete_file_record(file_id: str) -> bool:
    init_file_db()

    with _get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM files WHERE file_id = ?",
            (file_id,),
        )
        connection.commit()

    return cursor.rowcount > 0

def create_chat_session(
    session_id: str,
    user_id: str,
    title: str | None = None,
) -> None:
    init_file_db()
    now = datetime.now(UTC).isoformat()

    with _get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO chat_sessions(session_id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, title, now, now),
        )
        connection.commit()

def get_chat_session(session_id: str) -> dict[str, str] | None:
    init_file_db()

    with _get_connection() as connection:
        row = connection.execute(
            """
            SELECT session_id, user_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()

    return dict(row) if row else None

def touch_chat_session(session_id: str, user_id: str) -> None:
    init_file_db()
    now = datetime.now(UTC).isoformat()

    with _get_connection() as connection:
        connection.execute(
            """
            UPDATE chat_sessions
            SET updated_at = ?
            WHERE session_id = ?
            AND user_id = ?
            """,
            (now, session_id, user_id),
        )
        connection.commit()
    
def save_chat_message(session_id: str, role: str, content: str) -> None:
    init_file_db()
    created_at = datetime.now(UTC).isoformat()

    if role not in {"user", "assistant"}:
        raise ValueError("role 必须是 user 或 assistant")
        
    with _get_connection() as connection:
        connection.execute(
            """
            INSERT INTO chat_messages(session_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, created_at),
        )
        connection.execute(
            """
            UPDATE chat_sessions
            SET updated_at = ?
            WHERE session_id = ?
            """,
            (created_at, session_id),
        )
        connection.commit()

def list_recent_chat_messages(
    session_id: str,
    limit: int = 6,
) -> list[dict[str, str]]:
    init_file_db()

    with _get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, session_id, role, content, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()

    return [dict(row) for row in reversed(rows)]

def ensure_chat_session(
    session_id: str,
    user_id: str,
    title: str | None = None,
) -> None:
    init_file_db()

    existing_session = get_chat_session(session_id)
    if existing_session and existing_session["user_id"] != user_id:
        raise ValueError("session_id 已被其他用户使用")

    create_chat_session(
        session_id=session_id,
        user_id=user_id,
        title=title,
    )
    return 

def list_chat_sessions(user_id: str | None = None) -> list[dict[str, str]]:
    init_file_db()

    query = """
        SELECT session_id, user_id, title, created_at, updated_at
        FROM chat_sessions
    """
    params: tuple[str, ...] = ()

    if user_id:
        query += " WHERE user_id = ?"
        params = (user_id,)

    query += " ORDER BY updated_at DESC"

    with _get_connection() as connection:
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]

def delete_chat_messages(session_id: str) -> int:
    init_file_db()

    with _get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM chat_messages
            WHERE session_id = ?
            """,
            (session_id,),
        )
        connection.commit()

    return cursor.rowcount
