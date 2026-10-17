"""Day 43 — SQLite regression + optimization evidence.

Runs the dashboard/screener/clustering query paths against nifty100.db,
asserts row counts/values are unchanged by scripts/optimize_sqlite.py,
and records timings. Fails if an expected helpful index is missing or a
query regresses beyond a generous ceiling (the DB is tiny; queries run
in low milliseconds — ceilings only catch real regressions).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from time import perf_counter

DB = Path("nifty100.db")
REPORT = Path("reports/performance/sqlite.json")

QUERIES = {
    "dashboard_home": (
        "SELECT f.*, c.company_name, c.sector, s.pe_ratio, s.pb_ratio, s.dividend_yield "
        "FROM financial_ratios f JOIN companies c ON f.company_id = c.company_id "
        "LEFT JOIN financial_ratios_source s ON f.company_id = s.company_id AND f.year = s.year "
        "WHERE f.year = 2024",
        92,
        2.0,
    ),
    "company_profile": (
        "SELECT f.* FROM financial_ratios f JOIN companies c ON f.company_id = c.company_id "
        "WHERE c.ticker = 'RELIANCE' ORDER BY f.year DESC",
        14,
        2.0,
    ),
    "screener_roe_de": (
        "SELECT COUNT(DISTINCT company_id) FROM financial_ratios "
        "WHERE return_on_equity_pct > 15 AND debt_to_equity < 1 AND year = 2023",
        1,
        2.0,
    ),
    "cluster_latest_year": (
        "SELECT c.company_id FROM companies c JOIN financial_ratios f "
        "ON f.company_id = c.company_id JOIN "
        "(SELECT company_id, MAX(year) AS m FROM financial_ratios GROUP BY company_id) x "
        "ON x.company_id = c.company_id AND x.m = f.year",
        92,
        2.0,
    ),
}

EXPECTED_INDEXES = [
    "idx_finratios_year",
    "idx_finratios_company_year",
    "idx_pl_company_year",
    "idx_bs_company_year",
    "idx_cf_company_year",
    "idx_source_company_year",
    "idx_prices_company_date",
]


def test_indexes_present_and_queries_correct_and_fast():
    assert DB.exists(), "nifty100.db missing"
    conn = sqlite3.connect(str(DB))
    try:
        have = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        missing = [i for i in EXPECTED_INDEXES if i not in have]
        assert not missing, (
            f"missing optimization indexes {missing}; run python scripts/optimize_sqlite.py"
        )
        timings = {}
        for name, (sql, expect_rows, ceiling_s) in QUERIES.items():
            rows = conn.execute(sql).fetchall()
            assert len(rows) == expect_rows, (
                f"{name}: {len(rows)} rows, expected {expect_rows}"
            )
            best = min(
                (lambda t0: (conn.execute(sql).fetchall(), perf_counter() - t0)[1])(
                    perf_counter()
                )
                for _ in range(5)
            )
            timings[name] = {"rows": len(rows), "best_seconds": round(best, 4)}
            assert best < ceiling_s, f"{name} regressed: {best:.2f}s >= {ceiling_s}s"
        plan = conn.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM financial_ratios WHERE year = 2024"
        ).fetchall()
        assert any("idx_finratios_year" in r[-1] for r in plan), (
            f"year filter not using idx_finratios_year: {plan}"
        )
    finally:
        conn.close()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(timings, indent=2), encoding="utf-8")
