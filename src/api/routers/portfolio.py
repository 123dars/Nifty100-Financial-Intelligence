"""Portfolio and universe summary statistics endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter

from src.api.db import PROJECT_ROOT, query_all, query_one

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/stats")
def get_portfolio_stats():
    """Retrieve high-level universe statistics across the Nifty 100 universe."""
    # Counts
    companies_count = query_one("SELECT COUNT(*) AS total FROM companies")["total"]
    sectors_count = query_one("SELECT COUNT(DISTINCT sector) AS total FROM companies")[
        "total"
    ]

    # Financial averages (2024)
    fin_stats = query_one(
        """
        SELECT 
            ROUND(AVG(return_on_equity_pct), 2) AS avg_roe,
            ROUND(AVG(operating_profit_margin_pct), 2) AS avg_opm,
            ROUND(AVG(net_profit_margin_pct), 2) AS avg_npm,
            ROUND(AVG(debt_to_equity), 2) AS avg_debt_to_equity,
            ROUND(AVG(asset_turnover), 2) AS avg_asset_turnover
        FROM financial_ratios
        WHERE year = 2024
        """
    )

    # Cluster distribution
    cluster_dist = query_all(
        """
        SELECT cluster_id, cluster_name, COUNT(*) AS count
        FROM cluster_assignments
        GROUP BY cluster_id, cluster_name
        ORDER BY cluster_id ASC
        """
    )

    # Distress alerts count from output/distress_alerts.csv if exists
    distress_count = 0
    distress_path = PROJECT_ROOT / "output" / "distress_alerts.csv"
    if distress_path.exists():
        try:
            df = pd.read_csv(distress_path)
            distress_count = len(df)
        except Exception:
            distress_count = 0

    return {
        "universe_size": companies_count,
        "total_sectors": sectors_count,
        "financial_averages_2024": fin_stats,
        "cluster_distribution": cluster_dist,
        "distressed_companies_detected": distress_count,
    }
