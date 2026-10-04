

async def test_sub_districts_by_district(client, auth_headers, valid_district_id):
    resp = await client.get(
        f"/api/v1/districts/{valid_district_id}/sub-districts", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


async def test_sub_districts_district_not_found(client, auth_headers):
    resp = await client.get(
        "/api/v1/districts/99999/sub-districts", headers=auth_headers
    )
    assert resp.status_code == 404


async def test_get_sub_district(client, auth_headers, valid_sub_district_id):
    resp = await client.get(
        f"/api/v1/sub-districts/{valid_sub_district_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "village_count" in body


async def test_sub_district_not_found(client, auth_headers):
    resp = await client.get("/api/v1/sub-districts/99999", headers=auth_headers)
    assert resp.status_code == 404
