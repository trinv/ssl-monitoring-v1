"""
Simple Authentication Models
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Login request"""
    username: str
    password: str


class User(BaseModel):
    """User info (returned after login and in user list)"""
    id: int
    username: str
    full_name: Optional[str] = None
    role_id: int
    role_name: str  # 'admin' or 'user'
    is_active: bool = True

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response"""
    token: str
    user: User
    message: str = "Login successful"


class UserCreate(BaseModel):
    """Create new user (admin only)"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = None
    role_id: int = 2  # Default to 'user' role


class UserChangePassword(BaseModel):
    """Change password"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)
