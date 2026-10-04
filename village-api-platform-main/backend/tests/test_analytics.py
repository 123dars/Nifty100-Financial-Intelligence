

async def test_analytics_summary(client, auth_headers):
    resp = await client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_states" in body
    assert "total_districts" in body
    assert "total_sub_districts" in body
    assert "total_villages" in body
    assert body["total_states"] >= 1


async def test_analytics_top_states(client, auth_headers):
    resp = await client.get("/api/v1/analytics/top-states", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "top_states" in body
    assert isinstance(body["top_states"], list)


async def test_analytics_top_states_limit(client, auth_headers):
    resp = await client.get(
        "/api/v1/analytics/top-states", params={"limit": 5}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["top_states"]) <= 5


async def test_analytics_state(client, auth_headers, valid_state_id):
    resp = await client.get(
        f"/api/v1/analytics/state/{valid_state_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "district_count" in body
    assert "sub_district_count" in body
    assert "village_count" in body


async def test_analytics_state_not_found(client, auth_headers):
    resp = await client.get("/api/v1/analytics/state/99999", headers=auth_headers)
    assert resp.status_code == 404
