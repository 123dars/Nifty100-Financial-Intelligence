"""Peer comparison and radar chart endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.db import PROJECT_ROOT, query_all, query_one

router = APIRouter(prefix="/peers", tags=["Peers"])


@router.get("/{ticker}")
def get_company_peers(ticker: str):
    """Retrieve peer comparison and KPI percentile rankings (radar chart data) for a company."""
    company = query_one(
        "SELECT company_id, ticker, company_name, sector, industry FROM companies WHERE UPPER(ticker) = UPPER(?) OR company_id = ?",
        (ticker, ticker),
    )
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    cid = company["company_id"]
    actual_ticker = company["ticker"]

    # Retrieve peer group name
    peer_info = query_one(
        "SELECT DISTINCT peer_group_name FROM peer_percentiles WHERE company_id = ? LIMIT 1",
        (cid,),
    )
    peer_group = peer_info["peer_group_name"] if peer_info else None

    # Retrieve percentiles for this company
    percentiles = query_all(
        """
        SELECT metric, value, percentile_rank, year
        FROM peer_percentiles
        WHERE company_id = ?
        ORDER BY metric ASC
        """,
        (cid,),
    )

    # Retrieve peers in the same peer group if known
    peer_companies = []
    if peer_group:
        peer_companies = query_all(
            """
            SELECT DISTINCT c.company_id, c.ticker, c.company_name, c.industry
            FROM peer_percentiles pp
            JOIN companies c ON pp.company_id = c.company_id
            WHERE pp.peer_group_name = ? AND pp.company_id != ?
            ORDER BY c.company_name ASC
            """,
            (peer_group, cid),
        )

    # Check if radar chart PNG is generated
    radar_path = (
        PROJECT_ROOT / "reports" / "radar_charts" / f"{actual_ticker}_radar.png"
    )
    has_radar_chart = radar_path.exists()

    return {
        "company": company,
        "peer_group": peer_group,
        "percentile_rankings": percentiles,
        "peer_companies": peer_companies,
        "has_radar_chart": has_radar_chart,
        "radar_image_url": f"/reports/radar_charts/{actual_ticker}_radar.png"
        if has_radar_chart
        else None,
    }
