"""Market Cap and Valuation endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter

from src.api.db import PROJECT_ROOT, query_all

router = APIRouter(prefix="/market-cap", tags=["Market Cap"])


@router.get("")
def get_market_cap_rankings():
    """List all companies ranked by Market Cap with valuation multiples and flags."""
    # Check if valuation_summary.xlsx is present
    summary_path = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
    if summary_path.exists():
        df = pd.read_excel(summary_path)
        raw_records = df.to_dict(orient="records")
        clean_records = []
        for row in raw_records:
            clean_row = {}
            for k, v in row.items():
                if pd.isna(v) or v != v:
                    clean_row[k] = None
                else:
                    clean_row[k] = v
            clean_records.append(clean_row)
        return {
            "total_companies": len(clean_records),
            "rankings": clean_records,
        }

    # Fallback to DB
    sql = """
    SELECT c.company_id, c.ticker, c.company_name, c.sector, s.pe_ratio, s.pb_ratio
    FROM companies c
    LEFT JOIN financial_ratios_source s ON c.company_id = s.company_id AND s.year = 2024
    ORDER BY c.company_name ASC
    """
    rows = query_all(sql)
    return {"total_companies": len(rows), "rankings": rows}
