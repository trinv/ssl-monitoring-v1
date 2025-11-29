"""
Simple Authentication Routes
- Login with username/password
- Logout
- Change password
- Admin: manage users
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import asyncpg

from auth.models import LoginRequest, LoginResponse, User, UserCreate, UserChangePassword
from auth.utils import hash_password, verify_password, generate_session_token
from auth.dependencies import get_current_user, get_db_pool


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Simple login: check username/password, return token
    """
    async with pool.acquire() as conn:
        # Get user from database
        user_row = await conn.fetchrow("""
            SELECT u.id, u.username, u.full_name, u.password_hash,
                   u.role_id, r.role_name, u.is_active
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = $1
        """, login_data.username)

        # Check if user exists
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Check if user is active
        if not user_row['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        # Verify password
        if not verify_password(login_data.password, user_row['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Generate session token
        session_token = generate_session_token()

        # Save session to database
        await conn.execute("""
            INSERT INTO sessions (user_id, session_token)
            VALUES ($1, $2)
        """, user_row['id'], session_token)

        # Return user info and token
        user = User(
            id=user_row['id'],
            username=user_row['username'],
            full_name=user_row['full_name'],
            role_id=user_row['role_id'],
            role_name=user_row['role_name'],
            is_active=user_row['is_active']
        )

        return LoginResponse(
            token=session_token,
            user=user,
            message="Login successful"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Logout: delete session
    """
    async with pool.acquire() as conn:
        # Delete all sessions for this user
        await conn.execute("""
            DELETE FROM sessions WHERE user_id = $1
        """, current_user.id)

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user info
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Change password (any user can change their own password)
    """
    async with pool.acquire() as conn:
        # Get current password hash
        row = await conn.fetchrow("""
            SELECT password_hash FROM users WHERE id = $1
        """, current_user.id)

        # Verify old password
        if not verify_password(password_data.old_password, row['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash new password
        new_hash = hash_password(password_data.new_password)

        # Update password
        await conn.execute("""
            UPDATE users SET password_hash = $1 WHERE id = $2
        """, new_hash, current_user.id)

        # Delete all sessions (force re-login)
        await conn.execute("""
            DELETE FROM sessions WHERE user_id = $1
        """, current_user.id)

    return {"message": "Password changed successfully. Please login again."}


# ==================== ADMIN ONLY ENDPOINTS ====================

@router.get("/users", response_model=List[User])
async def list_users(
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List all users (admin only)
    """
    # Check if user is admin
    if current_user.role_name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.id, u.username, u.full_name,
                   u.role_id, r.role_name, u.is_active, u.created_at
            FROM users u
            JOIN roles r ON u.role_id = r.id
            ORDER BY u.created_at DESC
        """)

        users = []
        for row in rows:
            users.append(User(
                id=row['id'],
                username=row['username'],
                full_name=row['full_name'],
                role_id=row['role_id'],
                role_name=row['role_name'],
                is_active=row['is_active']
            ))

        return users


@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create new user (admin only)
    """
    # Check if user is admin
    if current_user.role_name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Hash password
    password_hash = hash_password(user_data.password)

    async with pool.acquire() as conn:
        try:
            # Insert user
            row = await conn.fetchrow("""
                INSERT INTO users (username, password_hash, full_name, role_id)
                VALUES ($1, $2, $3, $4)
                RETURNING id, username, full_name, role_id, is_active
            """, user_data.username, password_hash, user_data.full_name, user_data.role_id)

            # Get role name
            role_row = await conn.fetchrow("""
                SELECT role_name FROM roles WHERE id = $1
            """, user_data.role_id)

            return User(
                id=row['id'],
                username=row['username'],
                full_name=row['full_name'],
                role_id=row['role_id'],
                role_name=role_row['role_name'],
                is_active=row['is_active']
            )

        except asyncpg.UniqueViolationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Delete user (admin only)
    """
    # Check if user is admin
    if current_user.role_name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Prevent deleting yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    async with pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM users WHERE id = $1
        """, user_id)

        if result == "DELETE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

    return {"message": "User deleted successfully"}


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Enable/Disable user (admin only)
    """
    # Check if user is admin
    if current_user.role_name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Prevent disabling yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account"
        )

    async with pool.acquire() as conn:
        # Toggle is_active
        row = await conn.fetchrow("""
            UPDATE users
            SET is_active = NOT is_active
            WHERE id = $1
            RETURNING is_active
        """, user_id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        status_text = "enabled" if row['is_active'] else "disabled"
        return {"message": f"User {status_text} successfully"}


@router.put("/users/{user_id}/change-role")
async def change_user_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Change user role (admin only)
    """
    # Check if user is admin
    if current_user.role_name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Prevent changing your own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Validate role_id (only 1=admin or 2=user)
    if role_id not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Use 1 for admin or 2 for user"
        )

    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE users SET role_id = $1 WHERE id = $2
        """, role_id, user_id)

        if result == "UPDATE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

    role_name = "admin" if role_id == 1 else "user"
    return {"message": f"User role changed to {role_name}"}
