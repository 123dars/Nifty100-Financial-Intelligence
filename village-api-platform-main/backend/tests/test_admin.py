import uuid

API_NAME = "admin-test"


async def _unique_user():
    return (
        f"nonadmin-{uuid.uuid4().hex[:8]}@example.com",
        "password123",
    )


async def _nonadmin_token(client):
    email, password = await _unique_user()
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "full_name": "Regular User"},
    )
    assert resp.status_code == 201
    assert resp.json()["user"]["is_admin"] is False
    return resp.json()["access_token"]


async def test_admin_requires_auth(client):
    resp = await client.get("/api/v1/admin/overview")
    assert resp.status_code == 401


async def test_admin_requires_admin_role(client, admin_token):
    token = await _nonadmin_token(client)
    resp = await client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_admin_overview(client, admin_headers):
    resp = await client.get("/api/v1/admin/overview", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "stats" in body
    assert "usage" in body
    assert "recent_logs" in body


async def test_admin_usage(client, admin_headers):
    resp = await client.get("/api/v1/admin/usage", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_requests"] >= 0
    assert "hourly_requests" in body
    assert "daily_requests" in body


async def test_admin_create_and_update_key(client, admin_headers):
    create = await client.post(
        "/api/v1/admin/keys",
        headers=admin_headers,
        json={"name": API_NAME, "rate_limit": 100},
    )
    assert create.status_code == 201
    body = create.json()
    assert "secret" in body
    key_id = body["id"]

    update = await client.patch(
        f"/api/v1/admin/keys/{key_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert update.status_code == 200
    assert update.json()["is_active"] is False

    revoke_again = await client.patch(
        f"/api/v1/admin/keys/{key_id}",
        headers=admin_headers,
        json={"is_active": True, "rate_limit": 5},
    )
    assert revoke_again.status_code == 200
    assert revoke_again.json()["is_active"] is True


async def test_admin_list_keys(client, admin_headers):
    resp = await client.get("/api/v1/admin/keys", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "count" in body
    assert body["count"] >= 1


async def test_admin_logs(client, admin_headers, auth_headers):
    await client.get("/api/v1/states", headers=auth_headers)
    resp = await client.get("/api/v1/admin/logs", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["count"] >= 1


async def test_admin_top_clients(client, admin_headers):
    resp = await client.get("/api/v1/admin/logs/top-clients", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_admin_users(client, admin_headers):
    resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1