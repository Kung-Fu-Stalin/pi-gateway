import logging
import secrets
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import select

from api.config import settings
from api.services.pac import render_pac
from api.database import async_session, get_db
from api.models import UIUser, ProxyUser, Domain, DomainStatus, UserRole
from api.routers import auth, domains, users, logs
from api.services.squid import write_domains

logger = logging.getLogger(__name__)


async def create_admin_if_not_exists() -> None:
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

        proxy_user = ProxyUser(
            ui_user_id=admin.id,
            pac_token=secrets.token_hex(32),
            proxy_user=settings.admin_username,
            proxy_pass=secrets.token_hex(16),
        )
        db.add(proxy_user)
        await db.commit()
        logger.info("Admin user created: %s", settings.admin_username)


async def sync_domains_file() -> None:
    try:
        async with async_session() as db:
            result = await db.execute(
                select(Domain).where(Domain.status == DomainStatus.approved)
            )
            domain_list = [d.domain for d in result.scalars().all()]
            write_domains(domain_list)
            logger.info("Synced %d domains to file", len(domain_list))
    except Exception as e:
        logger.warning("Failed to sync domains file: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_admin_if_not_exists()
    await sync_domains_file()
    yield


app = FastAPI(
    title="Pi Gateway API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"https://{settings.domain}", f"http://{settings.domain}", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(domains.router)
app.include_router(users.router)
app.include_router(logs.router)


@app.get("/healthz", tags=["system"])
async def healthz():
    return {"ok": True}


@app.get("/proxy.pac", tags=["proxy"])
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

    content = render_pac(domain_list, settings.domain)
    return Response(content=content, media_type="application/x-ns-proxy-autoconfig")
