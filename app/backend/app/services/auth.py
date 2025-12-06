"""Authentication service with JWT tokens."""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User

# Use bcrypt directly instead of passlib (which has initialization bugs)
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using bcrypt or SHA256 fallback."""
    if BCRYPT_AVAILABLE:
        # Truncate password to 72 bytes (bcrypt limit)
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    else:
        # Fallback to SHA256 with salt
        salt = secrets.token_hex(16)
        hash_input = f"{salt}{password}".encode('utf-8')
        password_hash = hashlib.sha256(hash_input).hexdigest()
        return f"sha256${salt}${password_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    if hashed_password.startswith("sha256$"):
        # SHA256 fallback verification
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        stored_hash = parts[2]
        hash_input = f"{salt}{plain_password}".encode('utf-8')
        computed_hash = hashlib.sha256(hash_input).hexdigest()
        return computed_hash == stored_hash
    elif BCRYPT_AVAILABLE:
        # bcrypt verification
        password_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    return False


def create_access_token(user_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=JWT_EXPIRE_HOURS))
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: Optional[str] = None
) -> tuple[Optional[User], Optional[str]]:
    """Register a new user with email/password."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    
    if existing:
        return None, "Email already registered"
    
    # Create user
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name or email.split("@")[0],
        auth_provider="email",
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user, None


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
) -> tuple[Optional[User], Optional[str]]:
    """Authenticate a user with email/password."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        return None, "Invalid email or password"
    
    if not user.password_hash:
        return None, "This account uses a different sign-in method"
    
    if not verify_password(password, user.password_hash):
        return None, "Invalid email or password"
    
    return user, None


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """Get user by ID."""
    from uuid import UUID
    try:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        return result.scalar_one_or_none()
    except ValueError:
        return None

