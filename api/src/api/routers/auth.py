from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from api.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, hash_token, get_current_user
)
from api.config import settings
from api.database import get_db
from api.models import UIUser, RefreshToken


router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UIUser).where(UIUser.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Удаляем старые refresh токены этого пользователя
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token()

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    ))

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400,
    )

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    token_hash = hash_token(token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Корректное сравнение timezone-aware datetime
    expires_at = db_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        await db.delete(db_token)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user = await db.get(UIUser, db_token.user_id)
    if not user:
        await db.delete(db_token)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    new_refresh = create_refresh_token()
    db_token.token_hash = hash_token(new_refresh)
    db_token.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400,
    )

    return TokenResponse(access_token=create_access_token(user.id, user.role))


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        token_hash = hash_token(token)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        db_token = result.scalar_one_or_none()
        if db_token:
            await db.delete(db_token)
            await db.commit()
    response.delete_cookie("refresh_token")
    return {"ok": True}


@router.get("/me")
async def me(user: UIUser = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "last_login": user.last_login,
    }


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    user: UIUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong password")
    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"ok": True}
