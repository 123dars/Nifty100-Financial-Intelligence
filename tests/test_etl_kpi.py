"""Day 41 — ETL & KPI Unit Tests.

Covers:
1. normalize_year() variations and edge cases
2. Loader database counts verification (companies, sectors, financial statements)
3. 20 Ratio edge cases
4. 14 Data Quality (DQ) rules
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    capex_intensity,
    capital_allocation_pattern,
    fcf_conversion_rate,
    free_cash_flow,
)
from src.analytics.ratios import (
    asset_turnover,
    debt_to_equity,
    interest_coverage_ratio,
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    return_on_equity,
)
from src.etl.normaliser import normalize_ticker, normalize_year

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "nifty100.db"


@pytest.fixture(scope="module")
def db_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


# ==============================================================================
# 1. normalize_year() Unit Tests
# ==============================================================================


def test_normalize_year_standard_int():
    assert normalize_year(2024) == 2024


def test_normalize_year_standard_str():
    assert normalize_year("2024") == 2024


def test_normalize_year_fy_prefix():
    assert normalize_year("FY24") == 2024
    assert normalize_year("FY2024") == 2024


def test_normalize_year_month_year():
    assert normalize_year("Mar-24") == 2024
    assert normalize_year("Dec 2012") == 2012


def test_normalize_year_split_range():
    assert normalize_year("2023-24") == 2024
    assert normalize_year("2023/24") == 2024


def test_normalize_year_ttm_returns_none():
    assert normalize_year("TTM") is None
    assert normalize_year("ttm") is None


def test_normalize_year_missing_or_none():
    assert normalize_year(None) is None
    assert normalize_year("") is None
    assert normalize_year("   ") is None
    assert normalize_year("N/A") is None


def test_normalize_ticker():
    assert normalize_ticker("tcs.ns") == "TCS"
    assert normalize_ticker(" INFY.BO ") == "INFY"
    assert normalize_ticker(None) is None


# ==============================================================================
# 2. Loader Counts Verification
# ==============================================================================


def test_loader_companies_count(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM companies")
    count = cur.fetchone()[0]
    assert count == 92, f"Expected 92 companies, found {count}"


def test_loader_sectors_count(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sectors")
    count = cur.fetchone()[0]
    assert count == 10, f"Expected 10 sectors, found {count}"


def test_loader_profitandloss_count(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM profitandloss")
    count = cur.fetchone()[0]
    assert count >= 1000, f"Expected >=1000 P&L rows, found {count}"


def test_loader_balancesheet_count(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM balancesheet")
    count = cur.fetchone()[0]
    assert count >= 1000, f"Expected >=1000 BS rows, found {count}"


def test_loader_cashflow_count(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cashflow")
    count = cur.fetchone()[0]
    assert count >= 1000, f"Expected >=1000 CF rows, found {count}"


def test_loader_financial_ratios_count(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM financial_ratios")
    count = cur.fetchone()[0]
    assert count >= 1000, f"Expected >=1000 ratio rows, found {count}"


# ==============================================================================
# 3. 20 Ratio Edge Cases
# ==============================================================================


def test_edge_case_01_npm_zero_denominator():
    assert net_profit_margin(100, 0) is None


def test_edge_case_02_npm_none_sales():
    assert net_profit_margin(100, None) is None


def test_edge_case_03_npm_negative_sales():
    # Negative sales should return None or handled without crashing
    res = net_profit_margin(50, -200)
    assert res is None or res == -25.0


def test_edge_case_04_npm_negative_profit():
    assert net_profit_margin(-50, 1000) == -5.0


def test_edge_case_05_opm_normal_and_mismatch():
    res = operating_profit_margin(100, 1000, db_opm_percentage=10.0)
    assert res == 10.0


def test_edge_case_06_roe_negative_equity():
    # Negative net worth -> None (or flagged, per project rules)
    assert return_on_equity(50, -200, 50) is None


def test_edge_case_07_roe_zero_equity():
    assert return_on_equity(50, 0, 0) is None


def test_edge_case_08_roa_zero_assets():
    assert return_on_assets(50, 0) is None


def test_edge_case_09_de_zero_debt():
    res, flag = debt_to_equity(0, 100, 400, is_financials=False)
    assert res == 0.0
    assert flag is False


def test_edge_case_10_de_financial_sector_exemption():
    res, flag = debt_to_equity(1200, 100, 100, is_financials=True)
    assert res == 6.0
    assert flag is False  # high leverage flag exempted for financials


def test_edge_case_11_de_high_leverage():
    res, flag = debt_to_equity(1200, 100, 100, is_financials=False)
    assert res == 6.0
    assert flag is True  # > 5.0 triggers high leverage


def test_edge_case_12_icr_zero_interest():
    res, label, warning = interest_coverage_ratio(200, 0, 0)
    assert res is None
    assert label == "Debt Free"
    assert warning is False


def test_edge_case_13_icr_warning_threshold():
    res, label, warning = interest_coverage_ratio(50, 0, 100)
    assert res == 0.5
    assert warning is True  # icr < 1.5 triggers warning flag


def test_edge_case_14_asset_turnover_zero_assets():
    assert asset_turnover(500, 0) is None


def test_edge_case_15_fcf_none_components():
    assert free_cash_flow(None, None) == 0
    assert free_cash_flow(500, None) == 500


def test_edge_case_16_capex_intensity_zero_sales():
    pct, label = capex_intensity(-100, 0)
    assert pct is None
    assert label is None


def test_edge_case_17_fcf_conversion_zero_operating_profit():
    assert fcf_conversion_rate(100, 0) is None
    assert fcf_conversion_rate(100, None) is None


def test_edge_case_18_cagr_turnaround_loss_to_profit():
    cagr, flag = calculate_cagr(-100, 200, 5)
    assert flag == "TURNAROUND"
    assert cagr is None


def test_edge_case_19_cagr_zero_base_year():
    cagr, flag = calculate_cagr(0, 150, 3)
    assert cagr is None
    assert flag == "ZERO_BASE"


def test_edge_case_20_capital_allocation_pattern_distress():
    pattern, label = capital_allocation_pattern(-200, 50, 150)
    assert label == "Distress Signal"


# ==============================================================================
# 4. 14 Data Quality (DQ) Rules
# ==============================================================================


def test_dq_01_company_id_uniqueness(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(company_id), COUNT(DISTINCT company_id) FROM companies")
    total, distinct = cur.fetchone()
    assert total == distinct and total > 0


def test_dq_02_pl_composite_key_uniqueness(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT company_id, year, COUNT(*) FROM profitandloss GROUP BY company_id, year HAVING COUNT(*) > 1"
    )
    duplicates = cur.fetchall()
    assert len(duplicates) == 0, (
        f"Found duplicate (company_id, year) in P&L: {duplicates}"
    )


def test_dq_03_bs_composite_key_uniqueness(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT company_id, year, COUNT(*) FROM balancesheet GROUP BY company_id, year HAVING COUNT(*) > 1"
    )
    duplicates = cur.fetchall()
    assert len(duplicates) == 0, (
        f"Found duplicate (company_id, year) in BS: {duplicates}"
    )


def test_dq_04_cf_composite_key_uniqueness(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT company_id, year, COUNT(*) FROM cashflow GROUP BY company_id, year HAVING COUNT(*) > 1"
    )
    duplicates = cur.fetchall()
    assert len(duplicates) == 0, (
        f"Found duplicate (company_id, year) in CF: {duplicates}"
    )


def test_dq_05_ratios_composite_key_uniqueness(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT company_id, year, COUNT(*) FROM financial_ratios GROUP BY company_id, year HAVING COUNT(*) > 1"
    )
    duplicates = cur.fetchall()
    assert len(duplicates) == 0, (
        f"Found duplicate (company_id, year) in financial_ratios: {duplicates}"
    )


def test_dq_06_fk_ratios_to_companies(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM financial_ratios WHERE company_id NOT IN (SELECT company_id FROM companies)"
    )
    orphan_count = cur.fetchone()[0]
    assert orphan_count == 0


def test_dq_07_fk_pnl_to_companies(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM profitandloss WHERE company_id NOT IN (SELECT company_id FROM companies)"
    )
    orphan_count = cur.fetchone()[0]
    assert orphan_count == 0


def test_dq_08_fk_balancesheet_to_companies(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM balancesheet WHERE company_id NOT IN (SELECT company_id FROM companies)"
    )
    orphan_count = cur.fetchone()[0]
    assert orphan_count == 0


def test_dq_09_fk_cashflow_to_companies(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM cashflow WHERE company_id NOT IN (SELECT company_id FROM companies)"
    )
    orphan_count = cur.fetchone()[0]
    assert orphan_count == 0


def test_dq_10_positive_total_assets(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM balancesheet WHERE total_assets <= 0")
    bad_rows = cur.fetchone()[0]
    # As documented in Sprint 1 Data Quality report, 1 historical warning exists (Company 2, 2014)
    assert bad_rows <= 1, f"Found {bad_rows} records with non-positive total assets"


def test_dq_11_balance_sheet_equity_liabilities_sanity(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM balancesheet WHERE total_assets > 0 AND equity IS NOT NULL AND borrowings IS NOT NULL AND (equity + borrowings) > (total_assets * 2.5)"
    )
    extreme_outliers = cur.fetchone()[0]
    assert extreme_outliers == 0, (
        f"Found extreme BS equation anomalies: {extreme_outliers}"
    )


def test_dq_12_company_tickers_format(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT ticker FROM companies WHERE ticker IS NULL OR ticker = ''")
    empty_tickers = cur.fetchall()
    assert len(empty_tickers) == 0


def test_dq_13_isin_format(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT isin FROM companies WHERE isin IS NOT NULL")
    for row in cur.fetchall():
        isin = row[0].strip()
        assert isin.startswith("IN") and len(isin) == 12, f"Invalid ISIN: {isin}"


def test_dq_14_peer_groups_fk(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM peer_groups WHERE company_id NOT IN (SELECT company_id FROM companies) OR peer_company_id NOT IN (SELECT company_id FROM companies)"
    )
    invalid_peers = cur.fetchone()[0]
    assert invalid_peers == 0
