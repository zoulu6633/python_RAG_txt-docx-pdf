from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from crud.user_server import (
    create_user,
    create_user_session,
    delete_expired_user_sessions,
    delete_user_session,
    get_user_by_id,
    get_user_by_session_token,
    get_user_by_username,
    update_user,
)
from model.user import User
from schemas import ChangePasswordRequest, LoginRequest, RegisterRequest, UserInfo


ACCESS_TOKEN_EXPIRE_HOURS = 24
PASSWORD_ITERATIONS = 100_000
bearer_scheme = HTTPBearer(auto_error=False)




def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)





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

# 注册新用户
async def register_user_async(
    db: AsyncSession,
    request: RegisterRequest,
) -> UserInfo:
    if len(request.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少需要 3 个字符")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要 6 个字符")
    existing_user = await get_user_by_username(db, request.username)
    if existing_user:
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = await create_user(
        db=db,
        username=request.username,
        password_hash=hash_password(request.password),
        display_name=request.display_name.strip() if request.display_name else None,
    )
    return UserInfo.model_validate(user)

# 删除过期的用户会话
async def delete_expired_user_sessions_async(db: AsyncSession) -> int:
    return await delete_expired_user_sessions(db, _utc_now())

# 创建访问令牌
async def create_access_token_async(db: AsyncSession, user_id: str) -> tuple[str, str]:
    await delete_expired_user_sessions_async(db)
    token = secrets.token_urlsafe(32)
    now = _utc_now()
    expires_at = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    await create_user_session(
        db=db,
        token=token,
        user_id=user_id,
        created_at=now,
        expires_at=expires_at,
    )
    return token, expires_at.isoformat()

# 用户登录
async def login_user_async(
    db: AsyncSession,
    request: LoginRequest,
) -> tuple[UserInfo, str, str]:
    user = await get_user_by_username(db, request.username)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    await update_user(db, user, last_login_at=_utc_now())
    token, expires_at = await create_access_token_async(db, user.user_id)
    return UserInfo.model_validate(user), token, expires_at


# 更新用户个人信息
async def update_user_profile_async(
    db: AsyncSession,
    user_id: str,
    display_name: str | None = None,
) -> dict[str, str | None]:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if display_name is None:
        raise HTTPException(status_code=400, detail="请提供需要更新的字段")

    user = await update_user(
        db=db,
        user=user,
        display_name=display_name.strip() or None,
    )
    return UserInfo.model_validate(user)


async def change_password_async(
    db: AsyncSession,
    user_id: str,
    request: ChangePasswordRequest,
) -> None:
    """修改密码：校验原密码 → 设置新密码。"""
    from crud.user_server import get_user_by_id
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if len(request.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")
    new_hash = hash_password(request.new_password)
    await update_user(db=db, user=user, password_hash=new_hash)


def parse_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="请先登录")
    if credentials.scheme.lower() != "bearer" or not credentials.credentials.strip():
        raise HTTPException(status_code=401, detail="登录凭证无效")
    return credentials.credentials.strip()


async def get_current_user_async(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | None]:
    token = parse_bearer_token(credentials)
    now = _utc_now()
    user = await get_user_by_session_token(db, token, now)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return UserInfo.model_validate(user)


async def get_current_token_async(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    return parse_bearer_token(credentials)


async def logout_user_async(
    token: str = Depends(get_current_token_async),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await delete_user_session(db, token)
    return {"message": "已退出登录"}
