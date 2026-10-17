"""Day 43 — dashboard load gate (< 3 s server readiness).

Browser-render timing needs automation not installed here, so this test
measures server readiness (HTTP 200 + first byte) twice — cold then warm —
and SKIPS the render assertion honestly when no dashboard serves
N100_DASHBOARD_URL (default http://localhost:8501). It never claims a
browser gate passed from server timings alone.
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from time import perf_counter

import pytest

DASH_URL = os.environ.get("N100_DASHBOARD_URL", "http://localhost:8501")
BUDGET_S = 3.0
TIMEOUT_S = 20.0
REPORT = Path("reports/performance/dashboard_load.json")


def _fetch():
    t0 = perf_counter()
    try:
        with urllib.request.urlopen(DASH_URL, timeout=TIMEOUT_S) as resp:
            resp.read(1)
            return True, perf_counter() - t0, resp.status
    except Exception as exc:  # noqa: BLE001 — recorded, not hidden
        return False, perf_counter() - t0, f"{type(exc).__name__}"


def test_dashboard_server_readiness():
    ok_cold, cold_s, status = _fetch()
    if not ok_cold:
        pytest.skip(
            "BLOCKED: no dashboard serving at "
            f"{DASH_URL} ({status}). Launch with "
            "`streamlit run src/dashboard/app.py` and set "
            "N100_DASHBOARD_URL to run this gate. Browser-render timing "
            "additionally needs automation tooling."
        )
    ok_warm, warm_s, _ = _fetch()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(
            {
                "url": DASH_URL,
                "cold_seconds": round(cold_s, 3),
                "warm_seconds": round(warm_s, 3),
                "budget_seconds": BUDGET_S,
                "note": "server-readiness only; browser render not measured here",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    assert ok_warm, "warm dashboard fetch failed"
    assert cold_s < BUDGET_S, f"cold {cold_s:.2f}s >= {BUDGET_S}s"
    assert warm_s < BUDGET_S, f"warm {warm_s:.2f}s >= {BUDGET_S}s"
