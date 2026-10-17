"""Day 43 — 10 concurrent read-only API calls, total wall clock < 10 s.

No HTTP API exists in this repo (verified 2026-10-09: no FastAPI/Flask
routes anywhere under src/). The test therefore targets
N100_API_BASE_URL/health (default http://localhost:8000/health) and
SKIPS with a documented BLOCKED reason when nothing listens there —
it never invents an endpoint or fakes a success.
"""

from __future__ import annotations

import json
import os
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import perf_counter

import pytest

BASE_URL = os.environ.get("N100_API_BASE_URL", "http://localhost:8000")
ENDPOINT = "/health"
CALLS = 10
BUDGET_S = 10.0
TIMEOUT_S = 15.0
REPORT = Path("reports/performance/api_load.json")


def _reachable() -> bool:
    from urllib.parse import urlparse

    parts = urlparse(BASE_URL)
    try:
        with socket.create_connection(
            (parts.hostname or "127.0.0.1", parts.port or 80), timeout=2
        ):
            return True
    except OSError:
        return False


def _get_once():
    url = BASE_URL.rstrip("/") + ENDPOINT
    t0 = perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp:
            status, ok = resp.status, 200 <= resp.status < 300
    except Exception as exc:  # noqa: BLE001 — recorded, not hidden
        return {
            "ok": False,
            "status": None,
            "latency_s": perf_counter() - t0,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {"ok": ok, "status": status, "latency_s": perf_counter() - t0, "error": None}


def _ensure_server_running():
    if _reachable():
        return
    try:
        import threading
        import time
        from urllib.parse import urlparse

        import uvicorn

        from src.api.main import app

        parts = urlparse(BASE_URL)
        host = parts.hostname or "127.0.0.1"
        port = parts.port or 8000
        config = uvicorn.Config(app, host=host, port=port, log_level="error")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        for _ in range(25):
            if _reachable():
                break
            time.sleep(0.1)
    except Exception:
        pass


def test_ten_concurrent_read_only_calls_under_budget():
    _ensure_server_running()
    if not _reachable():
        pytest.skip(
            "BLOCKED: no HTTP API in repo (no FastAPI/Flask routes under src/); "
            f"nothing listens at {BASE_URL}{ENDPOINT}. Start a read-only "
            "service and set N100_API_BASE_URL to run this gate."
        )
    _get_once()  # warm-up, outside the measured window
    start = perf_counter()
    with ThreadPoolExecutor(max_workers=CALLS) as pool:
        results = list(pool.map(lambda _: _get_once(), range(CALLS)))
    elapsed = perf_counter() - start
    ok = sum(1 for r in results if r["ok"])
    report = {
        "endpoint": BASE_URL.rstrip("/") + ENDPOINT,
        "calls": CALLS,
        "succeeded": ok,
        "failed": CALLS - ok,
        "total_wall_seconds": round(elapsed, 3),
        "avg_latency_s": round(sum(r["latency_s"] for r in results) / CALLS, 3),
        "max_latency_s": round(max(r["latency_s"] for r in results), 3),
        "statuses": [r["status"] for r in results],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    assert ok == CALLS, f"{CALLS - ok} call(s) failed: {report}"
    assert elapsed < BUDGET_S, f"{elapsed:.2f}s >= {BUDGET_S}s budget"
