

async def test_global_search(client, auth_headers):
    resp = await client.get(
        "/api/v1/search", params={"q": "raj"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "states" in body
    assert "districts" in body
    assert "sub_districts" in body
    assert "villages" in body


async def test_global_search_empty_query(client, auth_headers):
    resp = await client.get("/api/v1/search", params={"q": ""}, headers=auth_headers)
    assert resp.status_code == 422


async def test_global_search_nonexistent(client, auth_headers):
    resp = await client.get(
        "/api/v1/search", params={"q": "zzzznonexistent"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["states"] == []
    assert body["districts"] == []
    assert body["sub_districts"] == []
    assert body["villages"] == []
