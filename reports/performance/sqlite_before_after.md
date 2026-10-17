# Day 43 — SQLite before/after (nifty100.db, same machine, 5-7 runs each)

Measured 2026-10-09 (Windows, SQLite, DB ≈ 1.6 MB, financial_ratios = 1288 rows).

| Query | Before (median) | After (median) | Plan change |
|---|---|---|---|
| dashboard_home (92 rows, year=2024 + company + source join) | 0.62 ms | 0.38 ms | SCAN f → SEARCH f USING idx_finratios_year; source join → idx_source_company_year |
| company_profile RELIANCE (14 rows, ORDER BY year) | 0.08 ms | 0.06 ms | autoindex → idx_finratios_company_year (covering) |
| screener ROE>15 AND D/E<1 @2023 | 0.08 ms | 0.03 ms | SCAN → SEARCH USING idx_finratios_year |
| cluster latest-year-per-company (92 rows) | 0.15 ms | 0.17 ms | covering idx_finratios_company_year (same speed, stable) |

Notes:
- The database is tiny, so absolute gains are sub-millisecond; the value
  is plan stability (no full scans on the hot year-filter path) as data grows.
- Row counts verified identical before/after (see scripts/optimize_sqlite.py).
- Correctness gate: tests/performance/test_sqlite_performance.py asserts
  exact row counts + index use + generous anti-regression ceilings.
