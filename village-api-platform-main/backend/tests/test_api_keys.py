async def test_generate_api_key(client):
    resp = await client.post("/api/v1/keys/generate", json={"name": "test"})
    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert "key" in body
    assert "secret" in body
    assert body["key"].startswith("bol_")


async def test_generate_api_key_missing_name(client):
    resp = await client.post("/api/v1/keys/generate", json={})
    assert resp.status_code == 422


async def test_list_api_keys_requires_auth(client):
    resp = await client.get("/api/v1/keys")
    assert resp.status_code == 401