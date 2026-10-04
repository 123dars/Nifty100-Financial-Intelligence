from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import decode_access_token, verify_key_secret
from app.database import get_db
from app.models.api_key import ApiKey
from app.models.request_log import RequestLog
from app.models.user import User
from app.services.cache import cache_get_json, cache_set_json


# FastAPI security scheme for Swagger / Bearer authentication.
# auto_error=False lets us keep our existing custom 401 message.
_bearer_scheme = HTTPBearer(auto_error=False)

# In-memory fallback when Redis is unreachable for a single key
_api_key_cache_ttl = 300  # 5 minutes


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


async def _load_api_key_from_db(
    db: AsyncSession,
    api_key: str,
) -> ApiKey | None:
    """Fetch an API key row from the database."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.key == api_key)
    )
    return result.scalar_one_or_none()


async def verify_api_key(
    request: Request,
    x_api_key: str | None = Header(
        default=None,
        alias=settings.API_KEY_HEADER,
    ),
    x_api_secret: str | None = Header(
        default=None,
        alias="X-API-Secret",
    ),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:

    if not x_api_key:
        raise _unauthorized("Missing API key")

    # ── Try Redis cache first ─────────────────────────────────
    cache_key = f"apikey:{x_api_key}"
    cached = await cache_get_json(cache_key)

    api_key: ApiKey | None = None

    if cached is not None:
        # Reconstruct minimal ApiKey-like object for downstream use
        api_key = await _load_api_key_from_db(db, x_api_key)

    else:
        api_key = await _load_api_key_from_db(db, x_api_key)

        if api_key is not None:
            # Populate cache with the serialised key info
            await cache_set_json(
                cache_key,
                {
                    "id": api_key.id,
                    "key": api_key.key,
                    "name": api_key.name,
                    "is_active": api_key.is_active,
                    "plan": (
                        api_key.plan
                        if hasattr(api_key, "plan")
                        else "free"
                    ),
                },
                ttl=_api_key_cache_ttl,
            )

    if api_key is None or not api_key.is_active:
        raise HTTPException(
            status_code=403,
            detail="Invalid or inactive API key",
        )

    if (
        api_key.expires_at is not None
        and api_key.expires_at < datetime.now(UTC)
    ):
        raise HTTPException(
            status_code=403,
            detail="API key has expired",
        )

    # Keys created with a secret require the matching secret on every call.
    if api_key.secret_digest is not None and (
        not x_api_secret
        or not verify_key_secret(
            api_key.key,
            x_api_secret,
            api_key.secret_digest,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API secret",
        )

    # Enforce the per-window request rate limit.
    window_start = datetime.now(UTC) - timedelta(
        seconds=settings.RATE_LIMIT_WINDOW_SECONDS
    )

    recent_count = (
        await db.execute(
            select(func.count(RequestLog.id)).where(
                RequestLog.api_key_id == api_key.id,
                RequestLog.created_at >= window_start,
            )
        )
    ).scalar_one()

    if recent_count >= api_key.rate_limit:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit of {api_key.rate_limit} requests per "
                f"{settings.RATE_LIMIT_WINDOW_SECONDS // 3600}h exceeded"
            ),
        )

    # Attach plan to request.state for the rate-limit middleware
    plan = (
        getattr(api_key, "plan", "free")
        if hasattr(api_key, "plan")
        else "free"
    )

    request.state.plan = plan

    api_key.last_used_at = datetime.now(UTC)
    await db.commit()

    return api_key


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer_scheme
    ),
    db: AsyncSession = Depends(get_db),
) -> User:

    # No Authorization header
    if credentials is None:
        raise _unauthorized("Not authenticated")

    # Make sure the scheme is actually Bearer
    if credentials.scheme.lower() != "bearer":
        raise _unauthorized("Not authenticated")

    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except Exception:
        raise _unauthorized("Invalid or expired token") from None

    subject = payload.get("sub")

    if not subject:
        raise _unauthorized("Invalid token payload")

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise _unauthorized("Invalid token subject") from None

    user = await db.get(User, user_id)

    if user is None or not user.is_active:
        raise _unauthorized("User not found or inactive")

    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:

    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required",
        )

    return user