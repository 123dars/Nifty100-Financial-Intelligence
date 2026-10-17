"""Company endpoints: list, profile, P&L, balance sheet, cashflow, ratios, tearsheet download."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.db import PROJECT_ROOT, query_all, query_one

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("")
def list_companies(
    q: str | None = Query(None, description="Search by ticker or company name"),
    sector: str | None = Query(None, description="Filter by sector name"),
):
    """List all Nifty 100 companies with optional query search and sector filtering."""
    sql = "SELECT company_id, ticker, company_name, sector, industry, isin, website FROM companies WHERE 1=1"
    params = []
    if q:
        sql += " AND (ticker LIKE ? OR company_name LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    if sector:
        sql += " AND sector = ?"
        params.append(sector)
    sql += " ORDER BY company_id ASC"
    rows = query_all(sql, params)
    return {"total": len(rows), "companies": rows}


@router.get("/{ticker}/profile")
def get_company_profile(ticker: str):
    """Retrieve comprehensive profile for a single company."""
    company = query_one(
        "SELECT * FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    cid = company["company_id"]
    actual_ticker = company["ticker"]

    # Latest ratios
    latest_ratios = query_one(
        """
        SELECT f.*, s.pe_ratio, s.pb_ratio, s.dividend_yield
        FROM financial_ratios f
        LEFT JOIN financial_ratios_source s ON f.company_id = s.company_id AND f.year = s.year
        WHERE f.company_id = ?
        ORDER BY f.year DESC LIMIT 1
        """,
        (cid,),
    )

    # Cluster assignment
    cluster_info = query_one(
        "SELECT cluster_id, cluster_name, fiscal_year FROM cluster_assignments WHERE company_id = ? ORDER BY fiscal_year DESC LIMIT 1",
        (cid,),
    )

    # Pros and Cons
    pros_cons = query_all(
        "SELECT item_type, description FROM prosandcons WHERE company_id = ?",
        (cid,),
    )

    # Peer group
    peer_info = query_one(
        "SELECT DISTINCT peer_group_name FROM peer_percentiles WHERE company_id = ? LIMIT 1",
        (cid,),
    )

    return {
        "company": company,
        "latest_ratios": latest_ratios,
        "cluster": cluster_info,
        "peer_group": peer_info["peer_group_name"] if peer_info else None,
        "pros_and_cons": pros_cons,
    }


@router.get("/{ticker}/pnl")
def get_company_pnl(ticker: str):
    """Retrieve historical Profit & Loss statements for a company."""
    company = query_one(
        "SELECT company_id, ticker, company_name FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    records = query_all(
        "SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year DESC",
        (company["company_id"],),
    )
    return {"ticker": company["ticker"], "total_records": len(records), "pnl": records}


@router.get("/{ticker}/balance-sheet")
def get_company_balance_sheet(ticker: str):
    """Retrieve historical Balance Sheet statements for a company."""
    company = query_one(
        "SELECT company_id, ticker, company_name FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    records = query_all(
        "SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year DESC",
        (company["company_id"],),
    )
    return {
        "ticker": company["ticker"],
        "total_records": len(records),
        "balance_sheet": records,
    }


@router.get("/{ticker}/cashflow")
def get_company_cashflow(ticker: str):
    """Retrieve historical Cash Flow statements for a company."""
    company = query_one(
        "SELECT company_id, ticker, company_name FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    records = query_all(
        "SELECT * FROM cashflow WHERE company_id = ? ORDER BY year DESC",
        (company["company_id"],),
    )
    return {
        "ticker": company["ticker"],
        "total_records": len(records),
        "cashflow": records,
    }


@router.get("/{ticker}/ratios")
def get_company_ratios(ticker: str):
    """Retrieve historical Financial Ratios for a company."""
    company = query_one(
        "SELECT company_id, ticker, company_name FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    records = query_all(
        """
        SELECT f.*, s.pe_ratio, s.pb_ratio, s.dividend_yield
        FROM financial_ratios f
        LEFT JOIN financial_ratios_source s ON f.company_id = s.company_id AND f.year = s.year
        WHERE f.company_id = ?
        ORDER BY f.year DESC
        """,
        (company["company_id"],),
    )
    return {
        "ticker": company["ticker"],
        "total_records": len(records),
        "ratios": records,
    }


@router.get("/{ticker}/tearsheet")
def download_company_tearsheet(ticker: str):
    """Download the batch-generated PDF tearsheet for a company."""
    company = query_one(
        "SELECT ticker FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    actual_ticker = company["ticker"]
    pdf_path = (
        PROJECT_ROOT / "reports" / "tearsheets" / f"{actual_ticker}_tearsheet.pdf"
    )
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet PDF for {actual_ticker} not found on disk.",
        )

    return FileResponse(
        path=str(pdf_path),
        filename=f"{actual_ticker}_tearsheet.pdf",
        media_type="application/pdf",
    )
