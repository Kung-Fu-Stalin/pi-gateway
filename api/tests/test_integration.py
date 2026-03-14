from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from api.config import settings


async def test_approve_domain_writes_file(client: AsyncClient, admin_token: str, tmp_files: dict):
    # Создаём группу и домен
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

    # Approve
    with patch.object(settings, "domains_file", str(tmp_files["domains"])):
        response = await client.post(
            f"/api/groups/domains/{domain_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    assert response.status_code == 200

    # Проверяем что домен записан в файл
    content = Path(tmp_files["domains"]).read_text()
    assert "test.com" in content


async def test_reject_domain_not_in_file(client: AsyncClient, admin_token: str, tmp_files: dict):
    group = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "bad.com"}
    )
    group_id = group.json()["id"]

    domain = await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "bad.com"}
    )
    domain_id = domain.json()["id"]

    with patch.object(settings, "domains_file", str(tmp_files["domains"])):
        await client.post(
            f"/api/groups/domains/{domain_id}/reject",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "not allowed"}
        )

    content = Path(tmp_files["domains"]).read_text()
    assert "bad.com" not in content


async def test_create_user_writes_passwd(client: AsyncClient, admin_token: str, tmp_files: dict):
    with patch.object(settings, "htpasswd_file", str(tmp_files["passwd"])):
        response = await client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"username": "newuser", "password": "pass1234", "role": "user"}
        )
    assert response.status_code == 201

    content = Path(tmp_files["passwd"]).read_text()
    assert "newuser" in content


async def test_delete_user_removes_from_passwd(client: AsyncClient, admin_token: str, tmp_files: dict):
    with patch.object(settings, "htpasswd_file", str(tmp_files["passwd"])):
        create = await client.post(
            "/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"username": "todelete", "password": "pass1234", "role": "user"}
        )
        user_id = create.json()["id"]

        await client.delete(
            f"/api/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    content = Path(tmp_files["passwd"]).read_text()
    assert "todelete" not in content


async def test_pac_file_contains_approved_domains(client: AsyncClient, admin_token: str, tmp_files: dict):
    # Создаём и апрувим домен
    group = await client.post(
        "/api/groups",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "mysite.com"}
    )
    group_id = group.json()["id"]

    domain = await client.post(
        f"/api/groups/{group_id}/domains",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"domain": "mysite.com"}
    )
    domain_id = domain.json()["id"]

    with patch.object(settings, "domains_file", str(tmp_files["domains"])):
        await client.post(
            f"/api/groups/domains/{domain_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    # Получаем PAC токен
    pac_info = await client.get(
        "/api/users/me/pac",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    token = pac_info.json()["pac_url"].split("token=")[1]

    # Проверяем PAC файл
    pac_response = await client.get(f"/proxy.pac?token={token}")
    assert pac_response.status_code == 200
    assert "mysite.com" in pac_response.text
    assert "FindProxyForURL" in pac_response.text
