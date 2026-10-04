import uuid


async def _unique_email():
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


async def test_signup(client):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": await _unique_email(),
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["email"].endswith("@example.com")
    assert body["user"]["is_admin"] is False


async def test_signup_duplicate(client):
    email = await _unique_email()
    payload = {
        "email": email,
        "password": "password123",
        "full_name": "Dup User",
    }
    assert (await client.post("/api/v1/auth/signup", json=payload)).status_code == 201
    resp = await client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 409


async def test_login_success(client):
    email = await _unique_email()
    password = "password123"
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": password, "full_name": "Login User"},
    )

    # New signups are PENDING_APPROVAL – approve directly so login succeeds
    from sqlalchemy import select

    from app.database import async_session
    from app.models.user import User

    async with async_session() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one()
        user.status = "active"
        await db.commit()

    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client):
    email = await _unique_email()
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "full_name": "Wrong User"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_me(client):
    email = await _unique_email()
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "full_name": "Me User"},
    )
    token = signup.json()["access_token"]
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == email


async def test_me_invalid_token(client):
    resp = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"}
    )
    assert resp.status_code == 401


async def test_me_missing_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_short_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": await _unique_email(),
            "password": "short",
            "full_name": "Weak User",
        },
    )
    assert resp.status_code == 422