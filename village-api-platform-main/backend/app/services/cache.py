"""Redis-backed caching service for API keys, query results, and session data.

Every public function is fail-safe: if Redis is unreachable the cache degrades
to a miss/no-op so the application keeps working against the database.
"""

from __future__ import annotations

import json
import typing

import redis.asyncio as redis

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("app.services.cache")

_pool: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Return a shared async Redis connection."""
    global _pool
    if _pool is None:
        _pool = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def close_redis() -> None:
    """Shut down the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def _degrade() -> None:
    """Log a single warning when Redis is unavailable."""
    logger.warning(
        "Redis unavailable – cache disabled for this operation "
        "(falling back to the database)"
    )


# ── Generic helpers ──────────────────────────────────────────────


async def cache_get(key: str) -> str | None:
    """Get a raw string value from cache."""
    try:
        r = await get_redis()
        return await r.get(key)
    except Exception:
        _degrade()
        return None


async def cache_set(key: str, value: str, ttl: int = 300) -> None:
    """Set a raw string value with a TTL in seconds (default 5 min)."""
    try:
        r = await get_redis()
        await r.set(key, value, ex=ttl)
    except Exception:
        _degrade()


async def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception:
        _degrade()


async def cache_get_json(key: str) -> typing.Any | None:
    """Get a JSON-deserialised value from cache."""
    raw = await cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


async def cache_set_json(key: str, value: typing.Any, ttl: int = 300) -> None:
    """Serialise *value* as JSON and cache it."""
    raw = json.dumps(value, default=str)
    await cache_set(key, raw, ttl=ttl)


async def cache_invalidate_pattern(pattern: str) -> int:
    """Delete all keys matching a glob pattern.  Returns count deleted."""
    try:
        r = await get_redis()
        keys: list[str] = []
        async for k in r.scan_iter(match=pattern):
            keys.append(k)
        if keys:
            return await r.delete(*keys)
        return 0
    except Exception:
        _degrade()
        return 0