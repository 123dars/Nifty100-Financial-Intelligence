

async def test_missing_api_key(client):
    resp = await client.get("/api/v1/states")
    assert resp.status_code == 401


async def test_invalid_api_key(client):
    resp = await client.get("/api/v1/states", headers={"X-API-Key": "invalid-key"})
    assert resp.status_code == 403


async def test_empty_api_key_header(client):
    resp = await client.get("/api/v1/states", headers={"X-API-Key": ""})
    assert resp.status_code == 401
