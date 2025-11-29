"""
Authentication Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List
import asyncpg
from datetime import datetime

from database import get_db_pool
from auth.models import (
    LoginRequest, LoginResponse, User, UserCreate,
    UserUpdate, UserChangePassword
)
from auth.utils import (
    hash_password, verify_password, generate_session_token,
    generate_token_expiry, validate_password_strength
)
from auth.dependencies import get_current_user, require_permission, require_role


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Login with username/password
    """
    async with pool.acquire() as conn:
        # Get user
        user_row = await conn.fetchrow("""
            SELECT
                u.id, u.username, u.email, u.full_name, u.password_hash,
                u.role_id, r.role_name, u.is_active,
                u.failed_login_attempts, u.locked_until,
                u.last_login_at, u.created_at, u.updated_at
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = $1 OR u.email = $1
        """, login_data.username)

        if not user_row:
            # Log failed attempt
            await conn.execute("""
                INSERT INTO audit_logs
                (username, action, success, ip_address, user_agent, details)
                VALUES ($1, 'login', FALSE, $2::INET, $3, $4::JSONB)
            """, login_data.username, request.client.host,
                request.headers.get('user-agent'),
                '{"reason": "user_not_found"}')

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Check if account is locked
        if user_row['locked_until'] and user_row['locked_until'] > datetime.now():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked. Please try again later."
            )

        # Check if active
        if not user_row['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )

        # Verify password
        if not verify_password(login_data.password, user_row['password_hash']):
            # Increment failed attempts
            failed_attempts = user_row['failed_login_attempts'] + 1
            locked_until = None

            # Lock account after 5 failed attempts (30 minutes)
            if failed_attempts >= 5:
                from datetime import timedelta
                locked_until = datetime.now() + timedelta(minutes=30)

            await conn.execute("""
                UPDATE users
                SET failed_login_attempts = $1, locked_until = $2
                WHERE id = $3
            """, failed_attempts, locked_until, user_row['id'])

            # Log failed attempt
            await conn.execute("""
                INSERT INTO audit_logs
                (user_id, username, action, success, ip_address, user_agent, details)
                VALUES ($1, $2, 'login', FALSE, $3::INET, $4, $5::JSONB)
            """, user_row['id'], user_row['username'],
                request.client.host, request.headers.get('user-agent'),
                f'{{"reason": "invalid_password", "failed_attempts": {failed_attempts}}}')

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Get permissions
        permissions = await conn.fetch("""
            SELECT p.permission_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = $1
        """, user_row['role_id'])

        permission_list = [p['permission_name'] for p in permissions]

        # Generate session token
        token = generate_session_token()
        expires_at = generate_token_expiry(hours=24)

        # Create session
        await conn.execute("""
            INSERT INTO sessions
            (user_id, session_token, ip_address, user_agent, expires_at)
            VALUES ($1, $2, $3::INET, $4, $5)
        """, user_row['id'], token, request.client.host,
            request.headers.get('user-agent'), expires_at)

        # Update user last login and reset failed attempts
        await conn.execute("""
            UPDATE users
            SET last_login_at = CURRENT_TIMESTAMP,
                failed_login_attempts = 0,
                locked_until = NULL
            WHERE id = $1
        """, user_row['id'])

        # Log successful login
        await conn.execute("""
            INSERT INTO audit_logs
            (user_id, username, action, success, ip_address, user_agent)
            VALUES ($1, $2, 'login', TRUE, $3::INET, $4)
        """, user_row['id'], user_row['username'],
            request.client.host, request.headers.get('user-agent'))

        user = User(
            id=user_row['id'],
            username=user_row['username'],
            email=user_row['email'],
            full_name=user_row['full_name'],
            role_id=user_row['role_id'],
            role_name=user_row['role_name'],
            is_active=user_row['is_active'],
            last_login_at=datetime.now(),
            created_at=user_row['created_at'],
            updated_at=user_row['updated_at'],
            permissions=permission_list
        )

        return LoginResponse(
            token=token,
            user=user,
            expires_at=expires_at
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Logout current user
    """
    # Get token from header
    auth_header = request.headers.get('authorization', '')
    token = auth_header.replace('Bearer ', '')

    async with pool.acquire() as conn:
        # Delete session
        await conn.execute("""
            DELETE FROM sessions WHERE session_token = $1
        """, token)

        # Log logout
        await conn.execute("""
            INSERT INTO audit_logs
            (user_id, username, action, success, ip_address, user_agent)
            VALUES ($1, $2, 'logout', TRUE, $3::INET, $4)
        """, current_user.id, current_user.username,
            request.client.host, request.headers.get('user-agent'))

    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: UserChangePassword,
    request: Request,
    current_user: User = Depends(get_current_user),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Change current user password
    """
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    async with pool.acquire() as conn:
        # Get current password hash
        row = await conn.fetchrow("""
            SELECT password_hash FROM users WHERE id = $1
        """, current_user.id)

        # Verify old password
        if not verify_password(password_data.old_password, row['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

        # Hash new password
        new_hash = hash_password(password_data.new_password)

        # Update password
        await conn.execute("""
            UPDATE users SET password_hash = $1 WHERE id = $2
        """, new_hash, current_user.id)

        # Log password change
        await conn.execute("""
            INSERT INTO audit_logs
            (user_id, username, action, success, ip_address, user_agent)
            VALUES ($1, $2, 'change_password', TRUE, $3::INET, $4)
        """, current_user.id, current_user.username,
            request.client.host, request.headers.get('user-agent'))

    return {"status": "success", "message": "Password changed successfully"}


# ==================== USER MANAGEMENT (Admin only) ====================

@router.get("/users", response_model=List[User])
async def list_users(
    current_user: User = Depends(require_permission("users.view")),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    List all users (Admin only)
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                u.id, u.username, u.email, u.full_name,
                u.role_id, r.role_name, u.is_active,
                u.last_login_at, u.created_at, u.updated_at
            FROM users u
            JOIN roles r ON u.role_id = r.id
            ORDER BY u.created_at DESC
        """)

        users = []
        for row in rows:
            permissions = await conn.fetch("""
                SELECT p.permission_name
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = $1
            """, row['role_id'])

            permission_list = [p['permission_name'] for p in permissions]

            users.append(User(
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
            ))

        return users


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(require_permission("users.create")),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Create new user (Admin only)
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    async with pool.acquire() as conn:
        # Check if username or email already exists
        existing = await conn.fetchrow("""
            SELECT id FROM users WHERE username = $1 OR email = $2
        """, user_data.username, user_data.email)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        row = await conn.fetchrow("""
            INSERT INTO users
            (username, email, password_hash, full_name, role_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, username, email, full_name, role_id,
                      is_active, last_login_at, created_at, updated_at
        """, user_data.username, user_data.email, password_hash,
            user_data.full_name, user_data.role_id)

        # Get role name
        role_row = await conn.fetchrow("""
            SELECT role_name FROM roles WHERE id = $1
        """, row['role_id'])

        # Get permissions
        permissions = await conn.fetch("""
            SELECT p.permission_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = $1
        """, row['role_id'])

        permission_list = [p['permission_name'] for p in permissions]

        # Log user creation
        await conn.execute("""
            INSERT INTO audit_logs
            (user_id, username, action, resource_type, resource_id,
             success, ip_address, user_agent, details)
            VALUES ($1, $2, 'create_user', 'user', $3, TRUE, $4::INET, $5, $6::JSONB)
        """, current_user.id, current_user.username, row['id'],
            request.client.host, request.headers.get('user-agent'),
            f'{{"new_username": "{user_data.username}"}}')

        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            role_name=role_row['role_name'],
            is_active=row['is_active'],
            last_login_at=row['last_login_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            permissions=permission_list
        )


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    current_user: User = Depends(require_permission("users.update")),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Update user (Admin only)
    """
    async with pool.acquire() as conn:
        # Check if user exists
        existing = await conn.fetchrow("""
            SELECT id FROM users WHERE id = $1
        """, user_id)

        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Build update query dynamically
        update_fields = []
        params = []
        param_count = 1

        if user_data.email is not None:
            update_fields.append(f"email = ${param_count}")
            params.append(user_data.email)
            param_count += 1

        if user_data.full_name is not None:
            update_fields.append(f"full_name = ${param_count}")
            params.append(user_data.full_name)
            param_count += 1

        if user_data.role_id is not None:
            update_fields.append(f"role_id = ${param_count}")
            params.append(user_data.role_id)
            param_count += 1

        if user_data.is_active is not None:
            update_fields.append(f"is_active = ${param_count}")
            params.append(user_data.is_active)
            param_count += 1

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        params.append(user_id)

        # Update user
        row = await conn.fetchrow(f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING id, username, email, full_name, role_id,
                      is_active, last_login_at, created_at, updated_at
        """, *params)

        # Get role name
        role_row = await conn.fetchrow("""
            SELECT role_name FROM roles WHERE id = $1
        """, row['role_id'])

        # Get permissions
        permissions = await conn.fetch("""
            SELECT p.permission_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = $1
        """, row['role_id'])

        permission_list = [p['permission_name'] for p in permissions]

        # Log update
        await conn.execute("""
            INSERT INTO audit_logs
            (user_id, username, action, resource_type, resource_id,
             success, ip_address, user_agent)
            VALUES ($1, $2, 'update_user', 'user', $3, TRUE, $4::INET, $5)
        """, current_user.id, current_user.username, user_id,
            request.client.host, request.headers.get('user-agent'))

        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            full_name=row['full_name'],
            role_id=row['role_id'],
            role_name=role_row['role_name'],
            is_active=row['is_active'],
            last_login_at=row['last_login_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            permissions=permission_list
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_permission("users.delete")),
    pool: asyncpg.Pool = Depends(get_db_pool)
):
    """
    Delete user (Admin only)
    """
    # Prevent deleting self
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    async with pool.acquire() as conn:
        # Check if user exists
        user = await conn.fetchrow("""
            SELECT username FROM users WHERE id = $1
        """, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Delete user (sessions and audit logs will cascade or be handled)
        await conn.execute("""
            DELETE FROM users WHERE id = $1
        """, user_id)

        # Log deletion
        await conn.execute("""
            INSERT INTO audit_logs
            (user_id, username, action, resource_type, resource_id,
             success, ip_address, user_agent, details)
            VALUES ($1, $2, 'delete_user', 'user', $3, TRUE, $4::INET, $5, $6::JSONB)
        """, current_user.id, current_user.username, user_id,
            request.client.host, request.headers.get('user-agent'),
            f'{{"deleted_username": "{user["username"]}"}}')

    return {"status": "success", "message": f"User {user['username']} deleted successfully"}
