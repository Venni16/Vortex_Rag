"""
security/auth.py — API Key and JWT bearer authentication dependencies.
"""

from fastapi import Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import get_settings

settings = get_settings()
_bearer_scheme = HTTPBearer(auto_error=False)


# ── API Key ───────────────────────────────────────────────────────────────────

async def verify_api_key(x_api_key: str = Header(..., alias="x-api-key")) -> str:
    """
    FastAPI dependency: validates the x-api-key header.
    Raise 403 if key is missing or wrong.
    """
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key.",
        )
    return x_api_key


# ── JWT Bearer ────────────────────────────────────────────────────────────────

async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency: validates a JWT bearer token.
    Returns the decoded payload on success.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ── Helper: create a JWT (for future /auth endpoint) ─────────────────────────

def create_access_token(data: dict) -> str:
    from datetime import datetime, timedelta, timezone

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {**data, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
