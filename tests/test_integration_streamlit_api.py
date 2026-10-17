"""Day 42 — Integration Tests: Streamlit Dashboard and REST API Compatibility.

Verifies end-to-end consistency between data models consumed by the
Streamlit dashboard and data served by the FastAPI backend.
"""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import app
from src.dashboard.utils.db import get_companies, get_ratios

PROJECT_ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_companies_consistency_streamlit_and_api():
    """Verify company count and tickers match between Streamlit DB query and API."""
    df_st = get_companies()
    resp = client.get("/api/companies")
    assert resp.status_code == 200
    api_data = resp.json()["companies"]

    assert len(df_st) == len(api_data) == 92
    st_tickers = set(df_st["ticker"].str.upper())
    api_tickers = {c["ticker"].upper() for c in api_data}
    assert st_tickers == api_tickers


def test_ratios_consistency_streamlit_and_api():
    """Verify ratio calculations match between Streamlit helper and API."""
    df_st = get_ratios("TCS", year=2024)
    resp = client.get("/api/companies/TCS/ratios")
    assert resp.status_code == 200
    api_ratios = resp.json()["ratios"]

    assert len(api_ratios) > 0
    latest_api = [r for r in api_ratios if r["year"] == 2024][0]
    st_roe = df_st.iloc[0]["return_on_equity_pct"]
    assert round(st_roe, 2) == round(latest_api["return_on_equity_pct"], 2)


def test_screener_preset_consistency_with_api():
    """Verify API screener preset output complies with Streamlit screener page requirements."""
    resp = client.get("/api/screener/presets/quality_compounder")
    assert resp.status_code == 200
    res = resp.json()
    assert 5 <= res["matched_count"] <= 50

    # Ensure required columns for dashboard rendering exist
    required_cols = {"company_id", "ticker", "company_name", "sector", "roe"}
    for company in res["matched_companies"]:
        assert required_cols.issubset(set(company.keys()))


def test_cluster_page_and_api_compatibility():
    """Verify cluster archetypes served by API match the 5 clusters used in Dashboard Page 09."""
    resp = client.get("/api/clusters")
    assert resp.status_code == 200
    clusters = resp.json()["clusters"]
    assert len(clusters) == 5
    cluster_ids = {c["cluster_id"] for c in clusters}
    assert cluster_ids == {0, 1, 2, 3, 4}


def test_peer_radar_chart_availability():
    """Verify peer radar data matches generated PNG artifacts for Streamlit display."""
    resp = client.get("/api/peers/TCS")
    assert resp.status_code == 200
    peer_data = resp.json()
    assert peer_data["has_radar_chart"] is True
    radar_file = PROJECT_ROOT / "reports" / "radar_charts" / "TCS_radar.png"
    assert radar_file.exists()


def test_all_streamlit_pages_compile_syntax():
    """Verify all 9 Streamlit page scripts have valid Python syntax and compile without error."""
    pages_dir = PROJECT_ROOT / "src" / "dashboard" / "pages"
    page_files = list(pages_dir.glob("*.py"))
    assert len(page_files) == 9, f"Expected 9 pages, found {len(page_files)}"

    for page in page_files:
        code = page.read_text(encoding="utf-8")
        # ast.parse raises SyntaxError if invalid
        parsed = ast.parse(code, filename=str(page))
        assert parsed is not None
