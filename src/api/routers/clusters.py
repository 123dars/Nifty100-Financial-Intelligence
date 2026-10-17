"""Stock Clustering and archetype endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.db import query_all, query_one

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("")
def list_clusters():
    """List the 5 KMeans clustering archetypes and summary metrics."""
    clusters = query_all(
        """
        SELECT 
            cluster_id, 
            cluster_name, 
            COUNT(DISTINCT company_id) AS company_count,
            fiscal_year
        FROM cluster_assignments
        GROUP BY cluster_id, cluster_name, fiscal_year
        ORDER BY cluster_id ASC
        """
    )
    return {
        "algorithm": "KMeans",
        "n_clusters": len(clusters),
        "clusters": clusters,
    }


@router.get("/{cluster_id}")
def get_cluster_members(cluster_id: int):
    """Retrieve all companies assigned to a specific cluster archetype."""
    cluster_meta = query_one(
        "SELECT DISTINCT cluster_id, cluster_name, fiscal_year FROM cluster_assignments WHERE cluster_id = ? LIMIT 1",
        (cluster_id,),
    )
    if not cluster_meta:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found.")

    members = query_all(
        """
        SELECT 
            c.company_id, c.ticker, c.company_name, c.sector, c.industry,
            f.return_on_equity_pct, f.operating_profit_margin_pct,
            f.net_profit_margin_pct, f.debt_to_equity, f.revenue_cagr_5yr, f.pat_cagr_5yr
        FROM cluster_assignments ca
        JOIN companies c ON ca.company_id = c.company_id
        LEFT JOIN financial_ratios f ON c.company_id = f.company_id AND f.year = ca.fiscal_year
        WHERE ca.cluster_id = ?
        ORDER BY c.company_name ASC
        """,
        (cluster_id,),
    )

    return {
        "cluster_id": cluster_id,
        "cluster_name": cluster_meta["cluster_name"],
        "fiscal_year": cluster_meta["fiscal_year"],
        "total_members": len(members),
        "members": members,
    }
