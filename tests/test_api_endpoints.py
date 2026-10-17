"""Day 42 — API Endpoints Verification Tests.

Verifies that all 16+ REST endpoints return expected HTTP status codes,
valid headers, and compliant JSON payloads.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_api_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert data["database_connected"] is True


def test_api_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "docs" in data


def test_api_companies_list():
    resp = client.get("/api/companies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 92
    assert len(data["companies"]) == 92


def test_api_companies_filter_query():
    resp = client.get("/api/companies?q=TCS")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(c["ticker"] == "TCS" for c in data["companies"])


def test_api_companies_filter_sector():
    resp = client.get("/api/companies?sector=Information Technology")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert all(c["sector"] == "Information Technology" for c in data["companies"])


def test_api_company_profile_valid():
    resp = client.get("/api/companies/TCS/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company"]["ticker"] == "TCS"
    assert "latest_ratios" in data
    assert "cluster" in data


def test_api_company_profile_404():
    resp = client.get("/api/companies/NONEXISTENT_TICKER/profile")
    assert resp.status_code == 404


def test_api_company_pnl():
    resp = client.get("/api/companies/TCS/pnl")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "TCS"
    assert data["total_records"] > 0
    assert "sales" in data["pnl"][0]


def test_api_company_balance_sheet():
    resp = client.get("/api/companies/TCS/balance-sheet")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_records"] > 0
    assert "total_assets" in data["balance_sheet"][0]


def test_api_company_cashflow():
    resp = client.get("/api/companies/TCS/cashflow")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_records"] > 0
    assert "operating_cash_flow" in data["cashflow"][0]


def test_api_company_ratios():
    resp = client.get("/api/companies/TCS/ratios")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_records"] > 0
    assert "return_on_equity_pct" in data["ratios"][0]


def test_api_company_tearsheet_download():
    resp = client.get("/api/companies/TCS/tearsheet")
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert len(resp.content) > 1000


def test_api_company_tearsheet_404():
    resp = client.get("/api/companies/INVALID_TICKER/tearsheet")
    assert resp.status_code == 404


def test_api_screener_presets_list():
    resp = client.get("/api/screener/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_presets"] >= 6


def test_api_screener_preset_execution():
    resp = client.get("/api/screener/presets/quality_compounder")
    assert resp.status_code == 200
    data = resp.json()
    assert 5 <= data["matched_count"] <= 50
    assert len(data["matched_companies"]) == data["matched_count"]


def test_api_screener_preset_404():
    resp = client.get("/api/screener/presets/non_existent_preset")
    assert resp.status_code == 404


def test_api_screener_custom_run():
    payload = {
        "filters": [
            {"metric": "roe", "operator": "gte", "threshold": 20.0},
            {"metric": "debt_to_equity", "operator": "lte", "threshold": 1.0},
        ],
        "debug": False,
    }
    resp = client.post("/api/screener/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "matched_companies" in data


def test_api_sectors_list():
    resp = client.get("/api/sectors")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sectors"] == 10


def test_api_sector_detail_valid():
    resp = client.get("/api/sectors/Information Technology")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_companies"] > 0


def test_api_sector_detail_404():
    resp = client.get("/api/sectors/NonExistentSector")
    assert resp.status_code == 404


def test_api_peers_valid():
    resp = client.get("/api/peers/TCS")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company"]["ticker"] == "TCS"
    assert "percentile_rankings" in data


def test_api_peers_404():
    resp = client.get("/api/peers/NONEXISTENT_TICKER")
    assert resp.status_code == 404


def test_api_market_cap():
    resp = client.get("/api/market-cap")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_companies"] > 0
    assert "rankings" in data


def test_api_portfolio_stats():
    resp = client.get("/api/portfolio/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["universe_size"] == 92
    assert data["total_sectors"] == 10
    assert len(data["cluster_distribution"]) == 5


def test_api_documents_valid():
    resp = client.get("/api/documents/TCS")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "TCS"
    assert "documents" in data


def test_api_documents_404():
    resp = client.get("/api/documents/NONEXISTENT_TICKER")
    assert resp.status_code == 404


def test_api_clusters_list():
    resp = client.get("/api/clusters")
    assert resp.status_code == 200
    data = resp.json()
    assert data["n_clusters"] == 5


def test_api_cluster_members_valid():
    resp = client.get("/api/clusters/0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cluster_id"] == 0
    assert data["total_members"] > 0


def test_api_cluster_members_404():
    resp = client.get("/api/clusters/999")
    assert resp.status_code == 404
