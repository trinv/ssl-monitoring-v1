"""
Simple Authentication Dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import asyncpg

from auth.simple_models import User


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
    Get current user from session token
    Simple: just check if token exists in sessions table
    """
    token = credentials.credentials

    async with pool.acquire() as conn:
        # Get user info from session token
        row = await conn.fetchrow("""
            SELECT u.id, u.username, u.full_name,
                   u.role_id, r.role_name, u.is_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            JOIN roles r ON u.role_id = r.id
            WHERE s.session_token = $1
        """, token)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please login again."
            )

        # Check if user is active
        if not row['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        return User(
            id=row['id'],
            username=row['username'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            role_name=row['role_name'],
            is_active=row['is_active']
        )


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role
    """
    if current_user.role_name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
