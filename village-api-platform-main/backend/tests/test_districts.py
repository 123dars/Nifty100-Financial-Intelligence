

async def test_districts_by_state(client, auth_headers, valid_state_id):
    resp = await client.get(
        f"/api/v1/states/{valid_state_id}/districts", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


async def test_districts_state_not_found(client, auth_headers):
    resp = await client.get("/api/v1/states/99999/districts", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_district(client, auth_headers, valid_district_id):
    resp = await client.get(
        f"/api/v1/districts/{valid_district_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "sub_district_count" in body


async def test_district_not_found(client, auth_headers):
    resp = await client.get("/api/v1/districts/99999", headers=auth_headers)
    assert resp.status_code == 404


async def test_districts_search(client, auth_headers, valid_state_id):
    resp = await client.get(
        f"/api/v1/states/{valid_state_id}/districts",
        params={"search": "a"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
