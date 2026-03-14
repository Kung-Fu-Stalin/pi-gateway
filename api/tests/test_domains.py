import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_list_groups(client: AsyncClient, admin_token: str):
    response = await client.get(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_create_group(client: AsyncClient, admin_token: str):
    response = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "ikea.com"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "ikea.com"


async def test_create_duplicate_group(client: AsyncClient, admin_token: str):
    await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "ikea.com"}
    )
    response = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "ikea.com"}
    )
    assert response.status_code == 400


async def test_add_domain_to_group(client: AsyncClient, admin_token: str):
    group = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "ikea.com"}
    )
    group_id = group.json()["id"]

    response = await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "ikea.com"}
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


async def test_approve_domain(client: AsyncClient, admin_token: str):
    group = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "ikea.com"}
    )
    group_id = group.json()["id"]

    domain = await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "ikea.com"}
    )
    domain_id = domain.json()["id"]

    response = await client.post(
        f"/api/groups/domains/{domain_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}


async def test_reject_domain(client: AsyncClient, admin_token: str):
    group = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test.com"}
    )
    group_id = group.json()["id"]

    domain = await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "test.com"}
    )
    domain_id = domain.json()["id"]

    response = await client.post(
        f"/api/groups/domains/{domain_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"reason": "Not needed"}
    )
    assert response.status_code == 200


async def test_delete_group(client: AsyncClient, admin_token: str):
    group = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "todelete.com"}
    )
    group_id = group.json()["id"]

    response = await client.delete(
        f"/api/groups/{group_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204