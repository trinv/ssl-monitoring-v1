"""
Authentication Utilities
"""
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Optional


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def generate_session_token() -> str:
    """Generate a secure random session token"""
    return secrets.token_urlsafe(32)


def generate_token_expiry(hours: int = 24) -> datetime:
    """Generate token expiration timestamp"""
    return datetime.now() + timedelta(hours=hours)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 100:
        return False, "Password must not exceed 100 characters"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numbers"

    return True, None
