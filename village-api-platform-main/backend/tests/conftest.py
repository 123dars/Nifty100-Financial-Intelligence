import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture(scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="session")
async def api_key(client):
    """Generate a new API key plus its secret via the endpoint."""
    resp = await client.post(
        "/api/v1/keys/generate", json={"name": "test-key"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "secret" in body
    return body


@pytest.fixture(scope="session")
def api_key_value(api_key):
    return api_key["key"]


@pytest.fixture(scope="session")
def api_secret_value(api_key):
    return api_key["secret"]


@pytest.fixture(scope="session")
def auth_headers(api_key_value, api_secret_value):
    return {"X-API-Key": api_key_value, "X-API-Secret": api_secret_value}


@pytest_asyncio.fixture(scope="session")
async def admin_token(client):
    """Guarantee an admin account exists and return its bearer token."""
    from sqlalchemy import select

    from app.database import async_session
    from app.models.user import User

    email = "admin@example.com"
    password = "password123"

    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "full_name": "Test Admin"},
    )
    assert signup.status_code in (201, 409)

    # Force the account to admin regardless of signup ordering.
    async with async_session() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one()
        if not user.is_admin:
            user.is_admin = True
        user.status = "active"
        await db.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture(scope="session")
async def valid_state_id(client, auth_headers):
    resp = await client.get("/api/v1/states", headers=auth_headers)
    assert resp.status_code == 200
    return resp.json()[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def valid_district_id(client, auth_headers, valid_state_id):
    resp = await client.get(
        f"/api/v1/states/{valid_state_id}/districts", headers=auth_headers
    )
    assert resp.status_code == 200
    return resp.json()[0]["id"]


@pytest_asyncio.fixture(scope="session")
async def valid_sub_district_id(client, auth_headers, valid_district_id):
    resp = await client.get(
        f"/api/v1/districts/{valid_district_id}/sub-districts", headers=auth_headers
    )
    assert resp.status_code == 200
    return resp.json()[0]["id"]