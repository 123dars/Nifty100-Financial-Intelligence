"""Unit tests — generic operators, missing values, observation selection."""

import math

import pytest

from src.screener.engine import (
    apply_single_filter,
    canonical_operator,
    evaluate_operator,
    is_missing,
    load_screener_config,
    select_screening_observation,
)


@pytest.mark.parametrize(
    "op,actual,expected,result",
    [
        ("gt", 5, 3, True),
        ("gt", 5, 5, False),
        ("gte", 5, 5, True),
        ("gte", 5, 6, False),
        ("lt", 5, 6, True),
        ("lt", 5, 5, False),
        ("lte", 5, 5, True),
        ("lte", 5, 4, False),
        ("eq", 5, 5, True),
        ("eq", 5, 6, False),
        ("neq", 5, 6, True),
        ("neq", 5, 5, False),
        # floats
        ("gte", 15.5, 15.0, True),
        ("lt", 0.09, 0.1, True),
        ("lte", 1.5, 1.5, True),
        # symbol aliases
        (">", 5, 3, True),
        (">=", 5, 5, True),
        ("<", 5, 6, True),
        ("<=", 5, 5, True),
        ("==", 5, 5, True),
        ("!=", 5, 6, True),
    ],
)
def test_operator_matrix(op, actual, expected, result):
    assert evaluate_operator(op, actual, expected) is result
    assert apply_single_filter(actual, op, expected) is result


def test_unknown_operator_raises():
    with pytest.raises(ValueError, match="Unknown screener operator"):
        canonical_operator("between")
    with pytest.raises(ValueError, match="Unknown screener operator"):
        evaluate_operator("between", 1, 2)


@pytest.mark.parametrize("bad", [None, float("nan"), float("inf"), float("-inf"), "", "N/A", "null", "abc"])
def test_missing_values_fail_every_operator(bad):
    for op in ("gt", "gte", "lt", "lte", "eq", "neq"):
        assert apply_single_filter(bad, op, 10) is False
    assert is_missing(bad) is True


def test_missing_never_equals_zero():
    # NULL != 0 : missing fails even `neq 0` (fail-closed, not SQL ternary logic).
    assert apply_single_filter(None, "neq", 0) is False
    assert apply_single_filter(float("nan"), "eq", 0) is False


def test_valid_zero_and_negatives_compare_normally():
    assert apply_single_filter(0, "eq", 0) is True
    assert apply_single_filter(0, "lte", 0.1) is True
    assert apply_single_filter(-5, "lt", 0) is True


def test_select_screening_observation_latest_per_company():
    rows = [
        {"company_id": 1, "year": 2021, "v": "old"},
        {"company_id": 1, "year": 2023, "v": "new"},
        {"company_id": 1, "year": 2022, "v": "mid"},
        {"company_id": 2, "year": 2020, "v": "only"},
        {"company_id": 3, "year": 2024, "v": "a"},
        {"company_id": 3, "year": 2024, "v": "a"},  # duplicate year tolerated
    ]
    out = select_screening_observation(rows)
    by_id = {r["company_id"]: r for r in out}
    assert len(out) == 3  # no duplicate companies
    assert by_id[1]["year"] == 2023
    assert by_id[2]["year"] == 2020
    assert by_id[3]["year"] == 2024


def test_screen_result_schema_single_company(tmp_path):
    """Ad-hoc screen returns the documented result object on a tiny temp DB."""
    import sqlite3

    from src.screener.engine import screen

    db = tmp_path / "mini.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE companies (company_id INTEGER PRIMARY KEY, ticker TEXT, company_name TEXT, sector TEXT, industry TEXT)")
    con.execute(
        "CREATE TABLE financial_ratios (company_id INTEGER, year INTEGER, return_on_equity_pct REAL,"
        " net_profit_margin_pct REAL, operating_profit_margin_pct REAL, debt_to_equity REAL,"
        " interest_coverage REAL, asset_turnover REAL, dividend_payout_ratio_pct REAL,"
        " total_debt_cr REAL, earnings_per_share REAL, revenue_cagr_5yr REAL,"
        " pat_cagr_5yr REAL, eps_cagr_5yr REAL, free_cash_flow_cr REAL)"
    )
    con.execute(
        "CREATE TABLE financial_ratios_source (company_id INTEGER, year INTEGER,"
        " pe_ratio REAL, pb_ratio REAL, dividend_yield REAL)"
    )
    con.execute("CREATE TABLE profitandloss (company_id INTEGER, year INTEGER, interest REAL, sales REAL, net_profit REAL)")
    con.execute("INSERT INTO companies VALUES (1, 'AAA', 'AAA Ltd', 'Industrials', 'X')")
    con.execute("INSERT INTO financial_ratios VALUES (1, 2024, 20, 15, 20, 0.5, 12, 1.0, 50, 100, 40, 10, 18, 15, 50)")
    con.execute("INSERT INTO financial_ratios_source VALUES (1, 2024, 20, 5, 2.5)")
    con.execute("INSERT INTO profitandloss VALUES (1, 2024, 100, 5000, 1000)")
    con.commit()
    con.close()

    cfg = load_screener_config()
    res = screen(
        filters=[{"metric": "roe", "operator": "gte", "value": 15}],
        db_path=db,
        config=cfg,
    )
    assert res["matched_count"] == 1
    assert res["total_input_companies"] == 1
    assert res["screening_year"] == 2024
    assert res["matched_companies"][0]["ticker"] == "AAA"
    assert math.isclose(res["matched_companies"][0]["roe"], 20)
