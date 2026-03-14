import pytest
from httpx import AsyncClient

from api.config import settings


pytestmark = pytest.mark.asyncio


async def test_list_users_as_admin(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(u["username"] == settings.admin_username for u in data)


async def test_list_users_no_auth(client: AsyncClient):
    response = await client.get("/api/users")
    assert response.status_code == 401


async def test_create_user(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "testuser", "password": "testpass123", "role": "user"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "pac_url" in data
    assert "proxy_user" in data
    assert "proxy_pass" in data


async def test_create_duplicate_user(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "testuser", "password": "testpass123", "role": "user"}
    )
    response = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "testuser", "password": "testpass123", "role": "user"}
    )
    assert response.status_code == 400


async def test_delete_user(client: AsyncClient, admin_token: str):
    create = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "todelete", "password": "testpass123", "role": "user"}
    )
    user_id = create.json()["id"]

    response = await client.delete(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204


async def test_reset_password(client: AsyncClient, admin_token: str):
    create = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "resetme", "password": "testpass123", "role": "user"}
    )
    user_id = create.json()["id"]

    response = await client.post(
        f"/api/users/{user_id}/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"password": "newpassword123"}
    )
    assert response.status_code == 200
    assert "pac_url" in response.json()
