import time

from fastapi import Request
from sqlalchemy import select

from app.core.logging import get_logger
from app.database import async_session
from app.models.api_key import ApiKey
from app.models.request_log import RequestLog

logger = get_logger("app.middleware.request_log")


async def _resolve_api_key(request: Request) -> tuple[int | None, str | None, bool]:
    """Resolve the API key attached to this call (cheap best-effort lookup)."""
    raw = request.headers.get("X-API-Key")
    if not raw:
        return None, None, True

    try:
        async with async_session() as db:
            result = await db.execute(
                select(ApiKey).where(ApiKey.key == raw).limit(1)
            )
            key = result.scalar_one_or_none()
            if key is None:
                return None, raw, True
            return key.id, key.name or raw, False
    except Exception:
        logger.exception("Failed to resolve API key for request log")
        return None, raw, True


async def track_request(request: Request, call_next):
    start = time.perf_counter()
    key_id, key_name, is_anonymous = None, None, True

    if "X-API-Key" in request.headers:
        key_id, key_name, is_anonymous = await _resolve_api_key(request)

    try:
        response = await call_next(request)
    except Exception:
        response = None
        raise
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        status_code = response.status_code if response is not None else 500
        try:
            async with async_session() as db:
                log_entry = RequestLog(
                    api_key_id=key_id,
                    api_key_name=key_name,
                    method=request.method,
                    path=request.url.path,
                    query_string=request.url.query or None,
                    status_code=status_code,
                    duration_ms=round(duration_ms, 3),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    is_anonymous=is_anonymous,
                )
                db.add(log_entry)
                await db.commit()
        except Exception:
            logger.exception("Failed to persist request log")

    logger.info(
        "%s %s -> %s (%.1fms, key=%s)",
        request.method,
        request.url.path,
        status_code,
        duration_ms,
        key_name or "anonymous",
    )

    return response