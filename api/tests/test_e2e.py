from pathlib import Path
from httpx import AsyncClient


async def test_delete_group_removes_from_db(client: AsyncClient, admin_token: str, db_session):
    r = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "todelete.com"}
    )
    assert r.status_code == 201
    group_id = r.json()["id"]

    r = await client.delete(
        f"/api/groups/{group_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 204

    r = await client.get("/api/groups", headers={"Authorization": f"Bearer {admin_token}"})
    assert not any(g["id"] == group_id for g in r.json())


async def test_delete_group_also_deletes_domains(client: AsyncClient, admin_token: str, db_session):
    r = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "withdomains.com"}
    )
    group_id = r.json()["id"]

    await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "withdomains.com"}
    )

    r = await client.delete(
        f"/api/groups/{group_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 204

    r = await client.get("/api/groups", headers={"Authorization": f"Bearer {admin_token}"})
    assert not any(g["id"] == group_id for g in r.json())


async def test_delete_domain_from_group(client: AsyncClient, admin_token: str):
    r = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "example.com"}
    )
    group_id = r.json()["id"]

    r = await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "example.com"}
    )
    domain_id = r.json()["id"]

    r = await client.delete(
        f"/api/groups/{group_id}/domains/{domain_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 204

    r = await client.get("/api/groups", headers={"Authorization": f"Bearer {admin_token}"})
    group = next(g for g in r.json() if g["id"] == group_id)
    assert not any(d["id"] == domain_id for d in group["domains"])


async def test_delete_approved_domain_removes_from_file(
    client: AsyncClient, admin_token: str, tmp_files: dict
):
    r = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "approved.com"}
    )
    group_id = r.json()["id"]

    r = await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "approved.com"}
    )
    domain_id = r.json()["id"]

    await client.post(
        f"/api/groups/domains/{domain_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert "approved.com" in Path(tmp_files["domains"]).read_text()

    await client.delete(
        f"/api/groups/{group_id}/domains/{domain_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert "approved.com" not in Path(tmp_files["domains"]).read_text()


async def test_delete_user(client: AsyncClient, admin_token: str):
    r = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "todelete", "password": "pass1234", "role": "user"}
    )
    assert r.status_code == 201
    user_id = r.json()["id"]

    r = await client.delete(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 204

    r = await client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert not any(u["id"] == user_id for u in r.json())


async def test_cannot_delete_self(client: AsyncClient, admin_token: str):
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    admin_id = r.json()["id"]

    r = await client.delete(
        f"/api/users/{admin_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r.status_code == 400


async def test_delete_user_removes_from_passwd(
    client: AsyncClient, admin_token: str, tmp_files: dict
):
    r = await client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"username": "passwduser", "password": "pass1234", "role": "user"}
    )
    user_id = r.json()["id"]

    assert "passwduser" in Path(tmp_files["passwd"]).read_text()

    await client.delete(
        f"/api/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert "passwduser" not in Path(tmp_files["passwd"]).read_text()