"""
Authentication Dependencies
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import asyncpg
from datetime import datetime

from auth.models import User


security = HTTPBearer()


async def get_db_pool():
    """Get database pool from main module"""
    import main
    return main.db_pool


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> User:
    """
    Get current authenticated user from session token
    """
    token = credentials.credentials

    async with pool.acquire() as conn:
        # Get session and user info
        row = await conn.fetchrow("""
            SELECT
                u.id, u.username, u.email, u.full_name,
                u.role_id, r.role_name, u.is_active,
                u.last_login_at, u.created_at, u.updated_at,
                s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            JOIN roles r ON u.role_id = r.id
            WHERE s.session_token = $1
        """, token)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

        # Check if session expired
        if row['expires_at'] < datetime.now():
            await conn.execute(
                "DELETE FROM sessions WHERE session_token = $1",
                token
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )

        # Check if user is active
        if not row['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )

        # Get user permissions
        permissions = await conn.fetch("""
            SELECT p.permission_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = $1
        """, row['role_id'])

        permission_list = [p['permission_name'] for p in permissions]

        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            role_name=row['role_name'],
            is_active=row['is_active'],
            last_login_at=row['last_login_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            permissions=permission_list
        )


def require_permission(permission: str):
    """
    Dependency to require specific permission
    """
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return current_user

    return permission_checker


def require_role(role_name: str):
    """
    Dependency to require specific role
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role_name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {role_name} required"
            )
        return current_user

    return role_checker


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    Used for optional authentication
    """
    if not authorization or not authorization.startswith('Bearer '):
        return None

    token = authorization.replace('Bearer ', '')

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT
                    u.id, u.username, u.email, u.full_name,
                    u.role_id, r.role_name, u.is_active,
                    u.last_login_at, u.created_at, u.updated_at,
                    s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                JOIN roles r ON u.role_id = r.id
                WHERE s.session_token = $1
            """, token)

            if not row or row['expires_at'] < datetime.now():
                return None

            permissions = await conn.fetch("""
                SELECT p.permission_name
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = $1
            """, row['role_id'])

            permission_list = [p['permission_name'] for p in permissions]

            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                full_name=row['full_name'],
                role_id=row['role_id'],
                role_name=row['role_name'],
                is_active=row['is_active'],
                last_login_at=row['last_login_at'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                permissions=permission_list
            )
    except Exception:
        return None
