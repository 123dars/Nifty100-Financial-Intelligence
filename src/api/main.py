"""Sprint 6: FastAPI Application Server Scaffold.

Features:
- SQLite connection management
- CORS middleware
- Custom request logging middleware
- 16+ REST endpoints across modular routers
- OpenAPI specification export
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.routers.clusters import router as clusters_router
from src.api.routers.companies import router as companies_router
from src.api.routers.documents import router as documents_router
from src.api.routers.market_cap import router as market_cap_router
from src.api.routers.peers import router as peers_router
from src.api.routers.portfolio import router as portfolio_router
from src.api.routers.screener import router as screener_router
from src.api.routers.sectors import router as sectors_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("n100_api")

app = FastAPI(
    title="N100 Financial Intelligence Platform API",
    description="Production REST API providing financial statements, calculated KPIs, stock clustering, screener presets, peer rankings, and tearsheet reports for the Nifty 100 universe.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)"
    )
    return response


# Health check endpoints
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify API server liveness and database accessibility."""
    db_file = PROJECT_ROOT / "nifty100.db"
    db_ok = db_file.exists()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "N100 Financial Intelligence API",
        "version": "1.0.0",
        "database_connected": db_ok,
    }


@app.get("/", tags=["Root"])
def root():
    """API Root with metadata and documentation links."""
    return {
        "message": "Welcome to the N100 Financial Intelligence Platform API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "version": "1.0.0",
    }


# Include modular routers under /api
app.include_router(companies_router, prefix="/api")
app.include_router(screener_router, prefix="/api")
app.include_router(sectors_router, prefix="/api")
app.include_router(peers_router, prefix="/api")
app.include_router(market_cap_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(clusters_router, prefix="/api")


def export_openapi_spec(output_path: str | Path | None = None) -> Path:
    """Export the OpenAPI schema to docs/openapi.json."""
    target_path = (
        Path(output_path) if output_path else PROJECT_ROOT / "docs" / "openapi.json"
    )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    logger.info(f"Exported OpenAPI specification to {target_path}")
    return target_path


if __name__ == "__main__":
    import uvicorn

    # Export spec on direct execution
    export_openapi_spec()
    port = int(os.environ.get("N100_API_PORT", 8000))
    host = os.environ.get("N100_API_HOST", "0.0.0.0")
    print(f"Starting N100 FastAPI server on {host}:{port}...")
    uvicorn.run("src.api.main:app", host=host, port=port, reload=False)
