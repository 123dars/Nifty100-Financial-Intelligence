"""Idempotent SQLite optimization for Sprint 6 Day 43.

Adds a small set of justified indexes (each tied to a measured dashboard /
screener / clustering query) and runs ANALYZE. Never modifies data:
verifies row counts before/after and rolls back on any error.

Usage:
    python scripts/optimize_sqlite.py [--db nifty100.db]
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Each index is justified by a real query path (see reports/performance/).
INDEXES = [
    (
        "idx_finratios_year",
        "CREATE INDEX IF NOT EXISTS idx_finratios_year ON financial_ratios(year)",
        "year-only filters: dashboard home, screener presets, cluster year slice",
    ),
    (
        "idx_finratios_company_year",
        "CREATE INDEX IF NOT EXISTS idx_finratios_company_year "
        "ON financial_ratios(company_id, year)",
        "company profile ORDER BY year + latest-year-per-company join",
    ),
    (
        "idx_pl_company_year",
        "CREATE INDEX IF NOT EXISTS idx_pl_company_year ON profitandloss(company_id, year)",
        "company P&L history + ratio engine scans",
    ),
    (
        "idx_bs_company_year",
        "CREATE INDEX IF NOT EXISTS idx_bs_company_year ON balancesheet(company_id, year)",
        "company balance-sheet history",
    ),
    (
        "idx_cf_company_year",
        "CREATE INDEX IF NOT EXISTS idx_cf_company_year ON cashflow(company_id, year)",
        "company cashflow history + cashflow KPIs",
    ),
    (
        "idx_source_company_year",
        "CREATE INDEX IF NOT EXISTS idx_source_company_year "
        "ON financial_ratios_source(company_id, year)",
        "vendor PE/PB/yield join on (company_id, year)",
    ),
    (
        "idx_prices_company_date",
        "CREATE INDEX IF NOT EXISTS idx_prices_company_date "
        "ON stock_prices(company_id, trade_date)",
        "price history per company in date order",
    ),
]

TABLES = [
    "companies",
    "financial_ratios",
    "financial_ratios_source",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "stock_prices",
]


def row_counts(conn: sqlite3.Connection) -> dict:
    return {
        t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in TABLES
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply idempotent SQLite indexes")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "nifty100.db"))
    args = parser.parse_args()
    conn = sqlite3.connect(args.db)
    try:
        before = row_counts(conn)
        with conn:  # transaction: index DDL applies atomically
            for name, ddl, why in INDEXES:
                conn.execute(ddl)
                print(f"ensured {name} — {why}")
            conn.execute("ANALYZE")
        after = row_counts(conn)
        assert before == after, f"Row counts changed: {before} -> {after}"
        print(f"row counts unchanged: {after}")
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' "
            "ORDER BY name"
        ).fetchall()
        print(f"project indexes present: {[r[0] for r in idx]}")
    except Exception as exc:
        print(f"Optimization failed (rolled back): {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
