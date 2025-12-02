"""
Authentication routes for SSL Monitor
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import logging

from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    session_manager,
    login_tracker
)
from backend.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

# ============================================
# Request/Response Models
# ============================================
class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "Admin@123456"
            }
        }

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: str
    user: dict

class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str

# ============================================
# Routes
# ============================================

@router.post("/login")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    User login endpoint
    Rate limited: 5/minute
    """
    client_ip = request.client.host
    identifier = f"{credentials.username}:{client_ip}"
    
    # Check if locked out
    if login_tracker.is_locked_out(identifier):
        logger.warning(f"❌ Login attempt from locked account: {identifier}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again in 15 minutes.",
            headers={"Retry-After": "900"}
        )
    
    try:
        # Query user from database
        from backend.models import User  # Import model
        
        stmt = select(User).where(User.username == credentials.username)
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            login_tracker.record_attempt(identifier, success=False)
            logger.warning(f"❌ Login failed - user not found: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash):
            login_tracker.record_attempt(identifier, success=False)
            logger.warning(f"❌ Login failed - wrong password: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"❌ Login attempt from inactive user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        # Record successful attempt
        login_tracker.record_attempt(identifier, success=True)
        
        # Create tokens
        token_data = create_access_token(user.id, user.username, user.role)
        refresh_token = create_refresh_token(user.id, user.username)
        
        # Create session
        session_id = session_manager.create_session(
            user.id,
            user.username,
            token_data["access_token"]
        )
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        
        logger.info(f"✅ User logged in: {credentials.username}")
        
        return LoginResponse(
            access_token=token_data["access_token"],
            token_type="bearer",
            expires_in=token_data["expires_in"],
            expires_at=token_data["expires_at"],
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout(
    request: Request,
    current_user: dict = Depends(verify_token)
):
    """Logout endpoint"""
    try:
        # Get session from request
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing token"
            )
        
        token = auth_header.split(" ")[1]
        
        # Invalidate session
        # You would need to store sessions in database/cache
        
        logger.info(f"✅ User logged out: {current_user['username']}")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/refresh")
async def refresh(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = verify_token(request.refresh_token)
        
        # Create new access token
        token_data = create_access_token(
            payload["user_id"],
            payload["username"],
            payload["role"]
        )
        
        logger.info(f"✅ Token refreshed for user: {payload['username']}")
        
        return token_data
        
    except Exception as e:
        logger.error(f"❌ Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.get("/me")
async def get_current_user(
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get current user info"""
    try:
        from backend.models import User
        
        stmt = select(User).where(User.id == current_user["user_id"])
        result = await db.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info"
        )