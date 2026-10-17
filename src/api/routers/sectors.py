"""Sector endpoints: sector summaries, aggregate KPIs, and company breakdown."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.db import query_all, query_one

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("")
def list_sectors():
    """List all sectors with company counts and aggregate financial performance."""
    sql = """
    SELECT 
        c.sector,
        COUNT(DISTINCT c.company_id) AS company_count,
        ROUND(AVG(f.return_on_equity_pct), 2) AS avg_roe,
        ROUND(AVG(f.operating_profit_margin_pct), 2) AS avg_opm,
        ROUND(AVG(f.net_profit_margin_pct), 2) AS avg_npm,
        ROUND(AVG(f.debt_to_equity), 2) AS avg_debt_to_equity
    FROM companies c
    LEFT JOIN financial_ratios f ON c.company_id = f.company_id AND f.year = 2024
    GROUP BY c.sector
    ORDER BY company_count DESC
    """
    rows = query_all(sql)
    return {"total_sectors": len(rows), "sectors": rows}


@router.get("/{sector_name}")
def get_sector_detail(sector_name: str):
    """Retrieve detailed company listing and metrics for a specific sector."""
    # Find matching companies
    companies = query_all(
        """
        SELECT 
            c.company_id, c.ticker, c.company_name, c.industry,
            f.return_on_equity_pct, f.operating_profit_margin_pct,
            f.net_profit_margin_pct, f.debt_to_equity,
            s.pe_ratio, s.pb_ratio
        FROM companies c
        LEFT JOIN financial_ratios f ON c.company_id = f.company_id AND f.year = 2024
        LEFT JOIN financial_ratios_source s ON c.company_id = s.company_id AND s.year = 2024
        WHERE LOWER(c.sector) = LOWER(?)
        ORDER BY c.company_name ASC
        """,
        (sector_name,),
    )
    if not companies:
        raise HTTPException(
            status_code=404, detail=f"Sector '{sector_name}' not found."
        )

    summary = query_one(
        """
        SELECT 
            COUNT(DISTINCT c.company_id) AS total_companies,
            ROUND(AVG(f.return_on_equity_pct), 2) AS avg_roe,
            ROUND(AVG(f.operating_profit_margin_pct), 2) AS avg_opm,
            ROUND(AVG(f.net_profit_margin_pct), 2) AS avg_npm
        FROM companies c
        LEFT JOIN financial_ratios f ON c.company_id = f.company_id AND f.year = 2024
        WHERE LOWER(c.sector) = LOWER(?)
        """,
        (sector_name,),
    )

    return {
        "sector": sector_name,
        "summary": summary,
        "companies": companies,
    }
