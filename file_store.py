from __future__ import annotations

import sqlite3
from datetime import datetime, UTC
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "app.db"


def _get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
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
            INSERT OR IGNORE INTO app_meta(key, value)
            VALUES ('file_seq', '0')
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
