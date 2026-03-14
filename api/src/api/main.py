import secrets
from contextlib import asynccontextmanager

import bcrypt
from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import selectinload
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.auth import get_current_user
from api.config import settings
from api.database import engine, async_session, Base, get_db
from api.models import UIUser, ProxyUser, Domain, DomainStatus, UserRole
from api.routers import auth, domains, users, logs
from api.services.squid import write_domains


async def create_admin_if_not_exists():
    async with async_session() as db:
        result = await db.execute(
            select(UIUser).where(UIUser.username == settings.admin_username)
        )
        if result.scalar_one_or_none():
            return

        password_hash = bcrypt.hashpw(
            settings.admin_password.encode(), bcrypt.gensalt()
        ).decode()

        admin = UIUser(
            username=settings.admin_username,
            password_hash=password_hash,
            role=UserRole.admin,
        )
        db.add(admin)
        await db.flush()

        proxy_pass = secrets.token_hex(16)
        pac_token = secrets.token_hex(32)

        proxy_user = ProxyUser(
            ui_user_id=admin.id,
            pac_token=pac_token,
            proxy_user=settings.admin_username,
            proxy_pass=proxy_pass,
        )
        db.add(proxy_user)
        await db.commit()


async def sync_domains_file():
    async with async_session() as db:
        result = await db.execute(
            select(Domain).where(Domain.status == DomainStatus.approved)
        )
        domain_list = [d.domain for d in result.scalars().all()]
        write_domains(domain_list)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_admin_if_not_exists()
    await sync_domains_file()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(domains.router)
app.include_router(users.router)
app.include_router(logs.router)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/proxy.pac")
async def proxy_pac(token: str = Query(...), db=Depends(get_db)):

    result = await db.execute(
        select(ProxyUser).where(ProxyUser.pac_token == token)
    )
    proxy = result.scalar_one_or_none()
    if not proxy:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(
        select(Domain).where(Domain.status == DomainStatus.approved)
    )
    domain_list = [d.domain for d in result.scalars().all()]

    rules = ", ".join(f'"{d}"' for d in domain_list)

    pac = f"""function FindProxyForURL(url, host) {{
    var domains = [{rules}];
    for (var i = 0; i < domains.length; i++) {{
        if (dnsDomainIs(host, domains[i]) || shExpMatch(host, "*." + domains[i])) {{
            return "PROXY {settings.domain}:3128";
        }}
    }}
    return "DIRECT";
}}
"""
    return Response(content=pac, media_type="application/x-ns-proxy-autoconfig")
