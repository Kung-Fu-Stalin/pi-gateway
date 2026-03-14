import secrets
from time import process_time_ns

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from api.auth import hash_password, require_admin, get_current_user
from api.config import settings
from api.database import get_db
from api.models import UIUser, ProxyUser, UserRole
from api.services.htpasswd import rebuild_htpasswd
from api.services.squid import reload_squid


router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.user


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    created_at: str
    pac_url: str | None = None
    proxy_user: str | None = None
    proxy_pass: str | None = None


async def rebuild_and_reload(db: AsyncSession) -> None:
    result = await db.execute(select(ProxyUser))
    proxy_users = result.scalars().all()
    users_data = [(p.proxy_user, p.proxy_pass) for p in proxy_users]
    rebuild_htpasswd(users_data)
    reload_squid()


@router.get("")
async def list_users(
    db: AsyncSession = Depends(get_db),
    user: UIUser = Depends(require_admin),
):
    result = await db.execute(
        select(UIUser).options(selectinload(UIUser.proxy_user))
    )
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "created_at": u.created_at,
            "last_login": u.last_login,
            "pac_url": (
                f"https://{settings.domain}/proxy.pac?token={u.proxy_user.pac_token}"
                if u.proxy_user else None
            ),
        }
        for u in users
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: UIUser = Depends(require_admin),
):
    existing = await db.execute(select(UIUser).where(UIUser.username == body.username))

    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = UIUser(
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()

    proxy_pass = secrets.token_hex(16)
    pac_token = secrets.token_hex(32)

    proxy_user = ProxyUser(
        ui_user_id=user.id,
        pac_token=pac_token,
        proxy_user=body.username,
        proxy_pass=proxy_pass,
    )
    db.add(proxy_user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

    await db.refresh(user)
    await db.refresh(proxy_user)
    await rebuild_and_reload(db)

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "pac_url": f"https://{settings.domain}/proxy.pac?token={pac_token}",
        "proxy_user": body.username,
        "proxy_pass": proxy_pass,
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UIUser = Depends(require_admin),
):
    user = await db.get(UIUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    await db.delete(user)
    await db.commit()

    result = await db.execute(
        select(ProxyUser).where(ProxyUser.ui_user_id != user_id)
    )
    remaining = [(p.proxy_user, p.proxy_pass) for p in result.scalars().all()]
    rebuild_htpasswd(remaining)
    reload_squid()


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UIUser = Depends(require_admin),
):
    user = await db.get(UIUser, user_id, options=[selectinload(UIUser.proxy_user)])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_proxy_pass = secrets.token_hex(16)
    new_pac_token = secrets.token_hex(32)

    if user.proxy_user:
        user.proxy_user.proxy_pass = new_proxy_pass
        user.proxy_user.pac_token = new_pac_token

    await db.commit()
    await rebuild_and_reload(db)

    return {
        "pac_url": f"https://{settings.domain}/proxy.pac?token={new_pac_token}",
        "proxy_user": user.username,
        "proxy_pass": new_proxy_pass,
    }


@router.get("/me/pac")
async def get_my_pac(
    user: UIUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProxyUser).where(ProxyUser.ui_user_id == user.id)
    )
    proxy = result.scalar_one_or_none()
    if not proxy:
        raise HTTPException(status_code=404, detail="No proxy user found")

    return {
        "pac_url": f"https://{settings.domain}/proxy.pac?token={proxy.pac_token}",
        "proxy_user": proxy.proxy_user,
        "proxy_pass": proxy.proxy_pass,
    }
