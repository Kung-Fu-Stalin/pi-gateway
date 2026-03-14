import pytest
from httpx import AsyncClient

from api.config import settings


pytestmark = pytest.mark.asyncio


async def test_healthz(client: AsyncClient):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


async def test_login_success(client: AsyncClient):
    response = await client.post("/api/auth/login", json={
        "username": settings.admin_username,
        "password": settings.admin_password
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    response = await client.post("/api/auth/login", json={
        "username": settings.admin_username,
        "password": "wrong"
    })
    assert response.status_code == 401


async def test_login_wrong_username(client: AsyncClient):
    response = await client.post("/api/auth/login", json={
        "username": "nonexistent",
        "password": settings.admin_password
    })
    assert response.status_code == 401


async def test_me(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == settings.admin_username
    assert data["role"] == "admin"


async def test_me_no_token(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_refresh_token(client: AsyncClient):
    login = await client.post("/api/auth/login", json={
        "username": settings.admin_username,
        "password": settings.admin_password
    })
    assert login.status_code == 200
    refresh_token = login.cookies.get("refresh_token")
    assert refresh_token is not None

    client.cookies.set("refresh_token", refresh_token)
    refresh_response = await client.post("/api/auth/refresh")
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()


async def test_logout(client: AsyncClient):
    await client.post("/api/auth/login", json={
        "username": settings.admin_username,
        "password": "test_admin_pass"
    })
    response = await client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
