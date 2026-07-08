from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from file_store import (
    create_user,
    delete_expired_user_sessions,
    delete_user_session,
    get_user_by_session_token,
    get_user_by_username,
    save_user_session,
)


ACCESS_TOKEN_EXPIRE_HOURS = 24
PASSWORD_ITERATIONS = 100_000
bearer_scheme = HTTPBearer(auto_error=False)


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _public_user(user: dict[str, str]) -> dict[str, str]:
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "created_at": user["created_at"],
    }


def validate_credentials(username: str, password: str) -> tuple[str, str]:
    normalized_username = _normalize_username(username)
    if len(normalized_username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少需要 3 个字符")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要 6 个字符")
    return normalized_username, password


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return (
        f"{PASSWORD_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(derived_key).decode('ascii')}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        iteration_text, salt_text, hash_text = password_hash.split("$", 2)
        salt = base64.b64decode(salt_text.encode("ascii"))
        expected_hash = base64.b64decode(hash_text.encode("ascii"))
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iteration_text),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(actual_hash, expected_hash)


def register_user(username: str, password: str) -> dict[str, str]:
    normalized_username, raw_password = validate_credentials(username, password)
    existing_user = get_user_by_username(normalized_username)
    if existing_user:
        raise HTTPException(status_code=409, detail="用户名已存在")

    created_user = create_user(
        username=normalized_username,
        password_hash=hash_password(raw_password),
    )
    return created_user


def create_access_token(user_id: str) -> tuple[str, str]:
    delete_expired_user_sessions()
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(UTC) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).isoformat()
    save_user_session(token=token, user_id=user_id, expires_at=expires_at)
    return token, expires_at


def login_user(username: str, password: str) -> tuple[dict[str, str], str, str]:
    normalized_username, raw_password = validate_credentials(username, password)
    user = get_user_by_username(normalized_username)
    if not user or not verify_password(raw_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token, expires_at = create_access_token(user["user_id"])
    return _public_user(user), token, expires_at


def parse_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="请先登录")

    if credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(status_code=401, detail="登录凭证无效")

    return credentials.credentials.strip()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str]:
    token = parse_bearer_token(credentials)
    user = get_user_by_session_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return _public_user(user)


def get_current_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    return parse_bearer_token(credentials)


def logout_user(token: str = Depends(get_current_token)) -> dict[str, str]:
    delete_user_session(token)
    return {"message": "已退出登录"}
