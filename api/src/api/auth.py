import hashlib
import secrets
from datetime import datetime, timezone, timedelta

import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.config import settings
from api.database import get_db
from api.models import UIUser, UserRole

bearer_scheme = HTTPBearer(auto_error=True)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(user_id), "role": role, "exp": expire},
        settings.api_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token() -> str:
    return secrets.token_hex(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.api_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if not payload.get("sub"):
            raise ValueError("Missing sub")
        return payload
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UIUser:
    payload = decode_token(credentials.credentials)
    user_id = int(payload["sub"])

    user = await db.get(UIUser, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def require_admin(user: UIUser = Depends(get_current_user)) -> UIUser:
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return user
