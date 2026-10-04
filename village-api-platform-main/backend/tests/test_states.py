

async def test_list_states(client, auth_headers):
    resp = await client.get("/api/v1/states", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 1


async def test_list_states_paginated(client, auth_headers):
    resp = await client.get(
        "/api/v1/states", params={"page": 1, "page_size": 5}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 5


async def test_get_state_by_id(client, auth_headers, valid_state_id):
    resp = await client.get(f"/api/v1/states/{valid_state_id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "district_count" in body


async def test_state_not_found(client, auth_headers):
    resp = await client.get("/api/v1/states/99999", headers=auth_headers)
    assert resp.status_code == 404


async def test_search_states(client, auth_headers):
    resp = await client.get(
        "/api/v1/states", params={"search": "raj"}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
