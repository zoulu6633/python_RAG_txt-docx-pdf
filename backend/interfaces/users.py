from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_async import (
    change_password_async,
    create_access_token_async,
    get_current_user_async,
    login_user_async,
    logout_user_async,
    register_user_async,
    update_user_profile_async,
    change_password_async,
)
from config.database import get_db
from schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UpdateUserRequest,
    UserInfo,
    ChangePasswordRequest,
)


router = APIRouter(tags=["users"])


@router.post("/register", response_model=TokenResponse)
async def register_api(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await register_user_async(
        db=db,
        request=request,
    )
    access_token, expires_at = await create_access_token_async(db, user.user_id)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserInfo.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login_api(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, expires_at = await login_user_async(
        db=db,
        request=request,
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        user=UserInfo.model_validate(user),
    )


@router.get("/me", response_model=UserInfo)
async def me_api(current_user: dict[str, str | None] = Depends(get_current_user_async)):
    return UserInfo.model_validate(current_user)


@router.put("/update", response_model=UserInfo)
async def update_me_api(
    request: UpdateUserRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    result = await update_user_profile_async(
        db=db,
        user_id=current_user.user_id,
        display_name=request.display_name,
    )
    return result


@router.put("/change-password")
async def change_password_api(
    request: ChangePasswordRequest,
    current_user: dict[str, str | None] = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_db),
):
    await change_password_async(
        db=db,
        user_id=current_user.user_id,
        request=request,
    )
    return {"message": "密码修改成功"}


@router.post("/logout", response_model=MessageResponse)
async def logout_api(result: dict[str, str] = Depends(logout_user_async)):
    return MessageResponse(**result)
