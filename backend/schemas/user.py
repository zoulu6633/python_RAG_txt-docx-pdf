from pydantic import BaseModel, ConfigDict
from datetime import datetime



class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    user_id: str
    username: str
    display_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
        )


class UpdateUserRequest(BaseModel):
    display_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
    user: UserInfo


class MessageResponse(BaseModel):
    message: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
