"""
Authentication Models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role_id: int = 2  # Default to 'user' role


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class User(UserBase):
    id: int
    role_id: int
    role_name: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    permissions: List[str] = []

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: User
    expires_at: datetime


class Session(BaseModel):
    id: int
    user_id: int
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
