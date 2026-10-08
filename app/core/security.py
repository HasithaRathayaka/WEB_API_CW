from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: str,
    scopes: List[str],
    role: str,
    jurisdiction_type: str = "national",
    jurisdiction_id: Optional[int] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a signed JWT token containing scopes and jurisdiction information
    to enforce RBAC and prevent cross-jurisdiction leakage.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "scopes": scopes,
        "role": role,
        "jurisdiction_type": jurisdiction_type,
        "jurisdiction_id": jurisdiction_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
