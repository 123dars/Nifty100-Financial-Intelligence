"""Redis-backed rate limiter – daily quota + per-minute burst.

Fail-open behaviour: if Redis is unreachable the request is allowed and a
default (empty) info block is returned, so the API stays available during
cache outages.  The database-backed per-window check in the auth middleware
still applies.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.logging import get_logger
from app.services.cache import get_redis

logger = get_logger("app.services.rate_limiter")


def _daily_key(api_key: str) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"rl:{api_key}:daily:{today}"


def _burst_key(api_key: str) -> str:
    return f"rl:{api_key}:burst"


def _default_info(daily_limit: int, burst_limit: int) -> dict:
    return {
        "remaining": daily_limit,
        "limit": daily_limit,
        "reset": int(datetime.now(UTC).timestamp()) + 3600,
        "burst_remaining": burst_limit,
        "burst_limit": burst_limit,
    }


async def check_rate_limit(
    api_key: str,
    daily_limit: int,
    burst_limit: int,
) -> tuple[bool, dict]:
    """Check whether *api_key* is within its limits.

    Returns (allowed, info_dict) where info_dict contains:
        remaining, limit, reset (unix epoch seconds), burst_remaining
    """
    try:
        r = await get_redis()

        daily_k = _daily_key(api_key)
        burst_k = _burst_key(api_key)

        pipe = r.pipeline()
        pipe.incr(daily_k)
        pipe.ttl(daily_k)
        pipe.incr(burst_k)
        pipe.expire(burst_k, 60)
        pipe.ttl(burst_k)
        results = await pipe.execute()

        daily_count: int = results[0]
        daily_ttl: int = results[1]
        burst_count: int = results[2]

        # First request – set a 24-hour expiry on the daily key
        if daily_ttl == -1:
            await r.expire(daily_k, 86400)
            daily_ttl = 86400

        reset_epoch = int(datetime.now(UTC).timestamp()) + max(daily_ttl, 0)
        remaining = max(daily_limit - daily_count, 0)
        burst_remaining = max(burst_limit - burst_count, 0)

        allowed = daily_count <= daily_limit and burst_count <= burst_limit

        info = {
            "remaining": remaining,
            "limit": daily_limit,
            "reset": reset_epoch,
            "burst_remaining": burst_remaining,
            "burst_limit": burst_limit,
        }
        return allowed, info
    except Exception:
        logger.warning(
            "Redis unavailable – rate limit check skipped (fail-open) "
            "for key %s…",
            api_key[:8],
        )
        return True, _default_info(daily_limit, burst_limit)


async def get_usage_counts(
    api_key: str,
) -> tuple[int, int]:
    """Return (daily_count, burst_count) for monitoring dashboards."""
    try:
        r = await get_redis()
        daily_k = _daily_key(api_key)
        burst_k = _burst_key(api_key)
        daily = await r.get(daily_k)
        burst = await r.get(burst_k)
        return int(daily or 0), int(burst or 0)
    except Exception:
        logger.warning("Redis unavailable – returning zero usage counts")
        return 0, 0
