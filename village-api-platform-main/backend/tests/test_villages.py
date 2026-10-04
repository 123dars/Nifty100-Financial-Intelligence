

async def test_villages_by_sub_district(client, auth_headers, valid_sub_district_id):
    resp = await client.get(
        f"/api/v1/sub-districts/{valid_sub_district_id}/villages", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


async def test_villages_sub_district_not_found(client, auth_headers):
    resp = await client.get(
        "/api/v1/sub-districts/99999/villages", headers=auth_headers
    )
    assert resp.status_code == 404


async def test_search_villages(client, auth_headers):
    resp = await client.get(
        "/api/v1/villages", params={"search": "luj"}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_global_villages_pagination(client, auth_headers):
    resp = await client.get(
        "/api/v1/villages",
        params={"page": 2, "page_size": 5},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 5
