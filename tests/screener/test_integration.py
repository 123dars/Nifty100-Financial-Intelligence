"""Integration test — full engine on a deterministic fixture DB."""

import sqlite3

import pytest

from src.screener.engine import load_screener_config, screen


@pytest.fixture()
def fixture_db(tmp_path):
    """9-company fixture exercising every archetype (read-only engine input)."""
    db = tmp_path / "fixture.db"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE companies (company_id INTEGER PRIMARY KEY, ticker TEXT,"
        " company_name TEXT, sector TEXT, industry TEXT)"
    )
    con.execute(
        "CREATE TABLE financial_ratios (company_id INTEGER, year INTEGER,"
        " return_on_equity_pct REAL, net_profit_margin_pct REAL,"
        " operating_profit_margin_pct REAL, debt_to_equity REAL, interest_coverage REAL,"
        " asset_turnover REAL, dividend_payout_ratio_pct REAL, total_debt_cr REAL,"
        " earnings_per_share REAL, revenue_cagr_5yr REAL, pat_cagr_5yr REAL,"
        " eps_cagr_5yr REAL, free_cash_flow_cr REAL)"
    )
    con.execute(
        "CREATE TABLE financial_ratios_source (company_id INTEGER, year INTEGER,"
        " pe_ratio REAL, pb_ratio REAL, dividend_yield REAL)"
    )
    con.execute("CREATE TABLE profitandloss (company_id INTEGER, year INTEGER, interest REAL, sales REAL, net_profit REAL)")

    companies = [
        # id, ticker, name, sector
        (1, "PASSCO", "Pass Co", "Industrials"),       # passes everything
        (2, "LOWROE", "Low Roe", "Industrials"),       # fails ROE
        (3, "FINBK", "Fin Bank", "Financials"),        # high D/E waived -> passes
        (4, "DEBTFR", "Debt Free", "Industrials"),    # debt 0, interest 0 -> ICR inf
        (5, "HIDEBT", "Hi Debt", "Materials"),         # high D/E non-fin -> fails
        (6, "HICOV", "Hi Cover", "Healthcare"),        # very high ICR
        (7, "ZEROINT", "Zero Int", "Energy"),          # interest 0 -> ICR inf
        (8, "MISROE", "Miss Roe", "Industrials"),      # missing ROE -> fails
        (9, "MULTIY", "Multi Year", "Industrials"),    # two years; latest (2024) passes
    ]
    con.executemany("INSERT INTO profitandloss VALUES (?,?,?,?,?)", [(c[0], 2024, 100, 5000, 1000) for c in companies])
    con.executemany(
        "INSERT INTO companies VALUES (?, ?, ?, ?, 'TestInd')", companies
    )

    def fr(cid, yr, roe, npm, opm, de, icr, debt):
        return (
            cid, yr, roe, npm, opm, de, icr, 1.0, 50.0, debt, 40.0,
            10.0, 18.0, 15.0, 50.0,
        )

    ratios = [
        fr(1, 2024, 20.0, 15.0, 20.0, 0.5, 12.0, 100.0),
        fr(2, 2024, 5.0, 15.0, 20.0, 0.5, 12.0, 100.0),
        fr(3, 2024, 18.0, 16.0, 22.0, 8.5, 2.0, 900.0),
        fr(4, 2024, 19.0, 18.0, 21.0, 0.0, None, 0.0),
        fr(5, 2024, 20.0, 15.0, 20.0, 4.0, 12.0, 800.0),
        fr(6, 2024, 22.0, 17.0, 23.0, 0.2, 636.0, 50.0),
        fr(7, 2024, 21.0, 16.0, 22.0, 0.3, None, 200.0),
        fr(8, 2024, None, 16.0, 22.0, 0.3, 12.0, 100.0),
        fr(9, 2022, 4.0, 2.0, 5.0, 5.0, 1.0, 900.0),   # old failing year
        fr(9, 2024, 20.0, 15.0, 20.0, 0.4, 11.0, 90.0),  # latest passing year
    ]
    con.executemany(
        "INSERT INTO financial_ratios VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ratios
    )
    con.executemany(
        "INSERT INTO financial_ratios_source VALUES (?,?,20.0,5.0,2.5)",
        [(c[0], 2024) for c in companies] + [(9, 2022)],
    )
    interests = [
        (1, 2024, 100.0),
        (2, 2024, 100.0),
        (3, 2024, 500.0),
        (4, 2024, 0.0),
        (5, 2024, 100.0),
        (6, 2024, 4.0),
        (7, 2024, 0.0),
        (8, 2024, 100.0),
        (9, 2022, 200.0),
        (9, 2024, 100.0),
    ]
    con.executemany("INSERT INTO profitandloss VALUES (?,?,?, 5000, 1000)", interests)
    con.commit()
    con.close()
    return db


def test_full_engine_selects_correct_companies(fixture_db):
    cfg = load_screener_config()
    filters = [
        {"metric": "roe", "operator": "gte", "value": 15},
        {"metric": "net_profit_margin", "operator": "gte", "value": 10},
        {"metric": "debt_to_equity", "operator": "lte", "value": 1.0},
    ]
    res = screen(filters=filters, db_path=fixture_db, config=cfg)
    tickers = sorted(c["ticker"] for c in res["matched_companies"])
    # PASSCO ok; FINBK waived D/E; DEBTFR debt-free; HICOV ok; ZEROINT ok; MULTIY latest ok
    assert tickers == ["DEBTFR", "FINBK", "HICOV", "MULTIY", "PASSCO", "ZEROINT"]
    # LOWROE fails ROE; HIDEBT fails D/E non-fin; MISROE missing fails
    assert "LOWROE" not in tickers
    assert "HIDEBT" not in tickers
    assert "MISROE" not in tickers


def test_full_engine_count_no_duplicates_and_years(fixture_db):
    cfg = load_screener_config()
    res = screen(
        filters=[{"metric": "roe", "operator": "gte", "value": 15}],
        db_path=fixture_db,
        config=cfg,
    )
    tickers = [c["ticker"] for c in res["matched_companies"]]
    assert len(tickers) == len(set(tickers))  # no duplicates
    years = {c["screening_year"] for c in res["matched_companies"]}
    assert years == {2024}  # latest observation selected (MULTIY 2022 ignored)


def test_full_engine_determinism(fixture_db):
    cfg = load_screener_config()
    filters = [{"metric": "roe", "operator": "gte", "value": 10}]
    a = screen(filters=filters, db_path=fixture_db, config=cfg)
    b = screen(filters=filters, db_path=fixture_db, config=cfg)
    assert [c["ticker"] for c in a["matched_companies"]] == [
        c["ticker"] for c in b["matched_companies"]
    ]


def test_source_db_not_mutated(fixture_db):
    import hashlib

    before = hashlib.md5(open(fixture_db, "rb").read()).hexdigest()
    cfg = load_screener_config()
    screen(filters=[{"metric": "roe", "operator": "gte", "value": 0}], db_path=fixture_db, config=cfg)
    after = hashlib.md5(open(fixture_db, "rb").read()).hexdigest()
    assert before == after
