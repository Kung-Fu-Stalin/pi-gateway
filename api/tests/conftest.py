import secrets
import tempfile
from pathlib import Path

import bcrypt
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from api.config import settings
from api.database import Base, get_db
from api.main import app
from api.models import UIUser, ProxyUser, UserRole
from unittest.mock import patch


@pytest_asyncio.fixture
async def tmp_files(tmp_path):
    domains_file = tmp_path / "domains.txt"
    passwd_file = tmp_path / "passwd"
    db_file = tmp_path / "test.db"
    domains_file.touch()
    passwd_file.touch()
    return {
        "domains": domains_file,
        "passwd": passwd_file,
        "db": db_file,
    }


@pytest_asyncio.fixture
async def db_session(tmp_files):
    db_url = f"sqlite+aiosqlite:///{tmp_files['db']}"
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        password_hash = bcrypt.hashpw(
            settings.admin_password.encode(), bcrypt.gensalt()
        ).decode()
        admin = UIUser(
            username=settings.admin_username,
            password_hash=password_hash,
            role=UserRole.admin,
        )
        session.add(admin)
        await session.flush()

        proxy_user = ProxyUser(
            ui_user_id=admin.id,
            pac_token=secrets.token_hex(32),
            proxy_user=settings.admin_username,
            proxy_pass=secrets.token_hex(16),
        )
        session.add(proxy_user)
        await session.commit()

        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session, tmp_files):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch.object(settings, "domains_file", str(tmp_files["domains"])), \
         patch.object(settings, "htpasswd_file", str(tmp_files["passwd"])), \
         patch("api.routers.domains.reload_squid"), \
         patch("api.routers.users.reload_squid"):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client):
    response = await client.post("/api/auth/login", json={
        "username": settings.admin_username,
        "password": settings.admin_password,
    })
    assert response.status_code == 200, response.json()
    return response.json()["access_token"]