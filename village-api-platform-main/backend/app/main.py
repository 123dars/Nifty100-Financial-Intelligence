from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.bootstrap import seed_super_admin
from app.core.logging import get_logger
from app.database import engine
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_log import track_request
from app.routers import (
    admin,
    analytics,
    api_keys,
    auth,
    autocomplete,
    districts,
    search,
    states,
    sub_districts,
    villages,
)
from app.services.cache import close_redis, get_redis

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify DB connection
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified")

    # Bootstrap super admin from ADMIN_EMAIL / ADMIN_PASSWORD
    await seed_super_admin()

    # Verify Redis connection
    r = await get_redis()
    await r.ping()
    logger.info("Redis connection verified")

    yield

    # Cleanup
    await close_redis()
    await engine.dispose()
    logger.info("Connections closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="India Location Data API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Rate limiting (outermost)
    app.add_middleware(RateLimitMiddleware)

    # Request logging middleware
    @app.middleware("http")
    async def request_logging_middleware(request, call_next):
        return await track_request(request, call_next)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_keys.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(autocomplete.router, prefix="/api/v1")
    app.include_router(states.router, prefix="/api/v1")
    app.include_router(districts.router, prefix="/api/v1")
    app.include_router(sub_districts.router, prefix="/api/v1")
    app.include_router(villages.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        return {"status": "ok"}

    return app


app = create_app()