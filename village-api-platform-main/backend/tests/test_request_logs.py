import uuid


async def test_request_is_logged(client, auth_headers, admin_headers):
    await client.get("/api/v1/states", headers=auth_headers)
    resp = await client.get("/api/v1/admin/logs", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    names = [item["api_key_name"] for item in body["items"]]
    assert any(names), "request logs should record which key made the call"


async def test_api_key_and_secret_required(client):
    """Keys generated with a secret must present both when calling APIs."""
    created = await client.post(
        "/api/v1/keys/generate", json={"name": f"sec-{uuid.uuid4().hex[:8]}"}
    )
    key = created.json()["key"]
    secret = created.json()["secret"]

    # Key without secret -> 403
    resp = await client.get("/api/v1/states", headers={"X-API-Key": key})
    assert resp.status_code == 403

    # Key with wrong secret -> 403
    resp = await client.get(
        "/api/v1/states", headers={"X-API-Key": key, "X-API-Secret": "wrong"}
    )
    assert resp.status_code == 403

    # Key with correct secret -> 200
    resp = await client.get(
        "/api/v1/states",
        headers={"X-API-Key": key, "X-API-Secret": secret},
    )
    assert resp.status_code == 200


async def test_legacy_key_without_secret_still_works(client):
    """Keys that predate the secret flow (no digest) keep working key-only."""

    from app.database import async_session
    from app.models.api_key import ApiKey

    legacy_key = f"legacy-{uuid.uuid4().hex}"
    async with async_session() as db:
        db.add(ApiKey(key=legacy_key, secret_digest=None, name="legacy"))
        await db.commit()

    resp = await client.get("/api/v1/states", headers={"X-API-Key": legacy_key})
    assert resp.status_code == 200


async def test_rate_limit_enforced(client, admin_headers):
    """A key with a tiny rate limit must trip 429 after exhausting it."""
    create = await client.post(
        "/api/v1/admin/keys",
        headers=admin_headers,
        json={"name": f"ratelimit-{uuid.uuid4().hex[:8]}", "rate_limit": 2},
    )
    assert create.status_code == 201
    headers = {
        "X-API-Key": create.json()["key"],
        "X-API-Secret": create.json()["secret"],
    }

    try:
        for _ in range(2):
            resp = await client.get("/api/v1/states", headers=headers)
            assert resp.status_code == 200

        resp = await client.get("/api/v1/states", headers=headers)
        assert resp.status_code == 429
    finally:
        # Restore a sane limit for any subsequent tests using this DB.
        await client.patch(
            f"/api/v1/admin/keys/{create.json()['id']}",
            headers=admin_headers,
            json={"rate_limit": 1000},
        )


async def test_inactive_key_rejected(client, auth_headers, admin_headers):
    create = await client.post(
        "/api/v1/admin/keys",
        headers=admin_headers,
        json={"name": f"inactive-{uuid.uuid4().hex[:8]}"},
    )
    key_id = create.json()["id"]
    guarded = {
        "X-API-Key": create.json()["key"],
        "X-API-Secret": create.json()["secret"],
    }
    assert (await client.get("/api/v1/states", headers=guarded)).status_code == 200

    await client.patch(
        f"/api/v1/admin/keys/{key_id}", headers=admin_headers, json={"is_active": False}
    )
    assert (await client.get("/api/v1/states", headers=guarded)).status_code == 403