"""
Authentication module for SSL Monitor
Handles JWT tokens, password hashing, and user authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
import logging
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# ============================================
# Password Hashing Configuration
# ============================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================
# JWT Configuration - From Environment
# ============================================
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

if not JWT_SECRET:
    raise ValueError("❌ JWT_SECRET not set in .env! This is CRITICAL for security.")

logger.info(f"✅ JWT configured with algorithm: {JWT_ALGORITHM}, expiry: {JWT_EXPIRATION_HOURS}h")

# ============================================
# Password Hashing Functions
# ============================================
def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

# ============================================
# JWT Token Functions
# ============================================
def create_access_token(
    user_id: int,
    username: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None
) -> Dict[str, str]:
    """
    Create JWT access token
    
    Args:
        user_id: User ID
        username: Username
        role: User role (user, admin)
        expires_delta: Custom expiration time
        
    Returns:
        Dictionary with token and expiry info
        
    Raises:
        ValueError: If JWT_SECRET not configured
    """
    if not JWT_SECRET:
        logger.error("JWT_SECRET not configured!")
        raise ValueError("JWT_SECRET not configured")
    
    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # Create payload
    payload = {
        "sub": str(user_id),           # Subject (user_id)
        "username": username,           # Username
        "role": role,                   # User role
        "iat": datetime.utcnow(),       # Issued at
        "exp": expire,                  # Expiration
        "iss": "ssl-monitor",           # Issuer
        "aud": "ssl-monitor-api"        # Audience
    }
    
    # Encode token
    try:
        encoded_jwt = jwt.encode(
            payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        
        logger.info(f"✅ Token created for user: {username}")
        
        return {
            "access_token": encoded_jwt,
            "token_type": "bearer",
            "expires_in": int((expire - datetime.utcnow()).total_seconds()),
            "expires_at": expire.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Token creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed"
        )

def verify_token(token: str) -> Dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token to verify
        
    Returns:
        Token payload (decoded token)
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Extract user info
        user_id = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")
        
        if not all([user_id, username, role]):
            logger.warning(f"❌ Invalid token payload: missing required fields")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        logger.debug(f"✅ Token verified for user: {username}")
        
        return {
            "user_id": int(user_id),
            "username": username,
            "role": role
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("❌ Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"❌ Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
        
    except Exception as e:
        logger.error(f"❌ Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed"
        )

# ============================================
# Refresh Token
# ============================================
def create_refresh_token(user_id: int, username: str) -> str:
    """
    Create refresh token (longer expiry than access token)
    
    Args:
        user_id: User ID
        username: Username
        
    Returns:
        Refresh token
    """
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days
    
    payload = {
        "sub": str(user_id),
        "username": username,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "exp": expire
    }
    
    try:
        refresh_token = jwt.encode(
            payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        
        logger.info(f"✅ Refresh token created for user: {username}")
        return refresh_token
        
    except Exception as e:
        logger.error(f"❌ Refresh token creation failed: {str(e)}")
        raise

# ============================================
# Session Management
# ============================================
class SessionManager:
    """Manage user sessions with expiry"""
    
    def __init__(self):
        """Initialize session manager"""
        self.sessions: Dict[str, Dict] = {}
    
    def create_session(self, user_id: int, username: str, token: str) -> str:
        """
        Create user session
        
        Args:
            user_id: User ID
            username: Username
            token: Access token
            
        Returns:
            Session ID
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "user_id": user_id,
            "username": username,
            "token": token,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        
        logger.info(f"✅ Session created for user: {username}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session info"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session expired
        if session["expires_at"] < datetime.utcnow():
            del self.sessions[session_id]
            logger.warning(f"❌ Session expired: {session_id}")
            return None
        
        # Update last activity
        session["last_activity"] = datetime.utcnow()
        
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate (logout) session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"✅ Session invalidated: {session_id}")
            return True
        
        return False

# Global session manager
session_manager = SessionManager()

# ============================================
# Password Validation
# ============================================
def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength requirements
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

# ============================================
# Rate Limiting for Failed Logins
# ============================================
class LoginAttemptTracker:
    """Track failed login attempts per IP/username"""
    
    def __init__(self, max_attempts: int = 5, lockout_minutes: int = 15):
        """
        Initialize tracker
        
        Args:
            max_attempts: Max failed attempts before lockout
            lockout_minutes: Lockout duration in minutes
        """
        self.max_attempts = max_attempts
        self.lockout_minutes = lockout_minutes
        self.attempts: Dict[str, list] = {}
    
    def record_attempt(self, identifier: str, success: bool = False):
        """Record a login attempt"""
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        now = datetime.utcnow()
        
        # Remove old attempts (older than lockout window)
        self.attempts[identifier] = [
            attempt for attempt in self.attempts[identifier]
            if (now - attempt).total_seconds() < self.lockout_minutes * 60
        ]
        
        if not success:
            self.attempts[identifier].append(now)
    
    def is_locked_out(self, identifier: str) -> bool:
        """Check if account is locked out"""
        if identifier not in self.attempts:
            return False
        
        now = datetime.utcnow()
        recent_attempts = [
            attempt for attempt in self.attempts[identifier]
            if (now - attempt).total_seconds() < self.lockout_minutes * 60
        ]
        
        return len(recent_attempts) >= self.max_attempts

# Global login attempt tracker
login_tracker = LoginAttemptTracker(max_attempts=5, lockout_minutes=15)