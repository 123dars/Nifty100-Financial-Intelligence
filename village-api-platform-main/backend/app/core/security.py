import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import settings

TOKEN_TYPE_ACCESS = "access"


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRES_MINUTES),
        "type": TOKEN_TYPE_ACCESS,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def generate_api_key() -> str:
    """Generate a cryptographically random API key."""
    return f"bol_{base64.urlsafe_b64encode(os.urandom(24)).decode().rstrip('=')}"


def generate_api_secret() -> str:
    """Generate a random API secret returned once at creation time."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip("=")


def sign_key_secret(key: str, secret: str) -> str:
    """Derive a verifiable HMAC digest for the key/secret pair for storage."""
    return hmac.new(
        secret.encode("utf-8"), key.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_key_secret(key: str, secret: str, digest: str) -> bool:
    expected = sign_key_secret(key, secret)
    return hmac.compare_digest(expected, digest)