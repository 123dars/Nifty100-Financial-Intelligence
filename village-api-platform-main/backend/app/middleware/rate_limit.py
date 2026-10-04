"""Rate-limiting middleware – delegates to the Redis-backed rate_limiter service."""

from __future__ import annotations

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.services.rate_limiter import check_rate_limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce daily + burst rate limits for API key-authenticated requests."""

    # Paths that are exempt from rate limiting
    _EXEMPT_PREFIXES = ("/health", "/docs", "/openapi.json", "/redoc")

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip non-API routes and exempt paths
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)

        if any(request.url.path.startswith(p) for p in self._EXEMPT_PREFIXES):
            return await call_next(request)

        api_key = request.headers.get(settings.API_KEY_HEADER)
        if not api_key:
            return await call_next(request)

        # Determine plan tier from request state (set by auth middleware)
        plan = getattr(request.state, "plan", "free")
        tier = settings.PLAN_LIMITS.get(plan, settings.PLAN_LIMITS["free"])

        allowed, info = await check_rate_limit(
            api_key,
            daily_limit=tier["daily"],
            burst_limit=tier["burst"],
        )

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Daily rate limit exceeded. Upgrade your plan.",
            )

        response = await call_next(request)

        # Attach rate-limit headers to every response
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response
