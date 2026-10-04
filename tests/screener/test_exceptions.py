"""Unit tests — Financial D/E exception + debt-free ICR edge cases."""

import math

import pytest

from src.screener.engine import (
    effective_interest_coverage,
    is_debt_free,
    is_financial_sector,
    load_screener_config,
    row_passes_filters,
    should_waive_de_filter,
)


@pytest.fixture()
def cfg():
    return load_screener_config()


def _row(sector="Industrials", de=0.5, icr=10.0, debt=100.0, interest=50.0, **kw):
    base = {
        "company_id": 1,
        "ticker": "TST",
        "sector": sector,
        "debt_to_equity": de,
        "interest_coverage_ratio": icr,
        "total_debt": debt,
        "interest_expense": interest,
    }
    base.update(kw)
    return base


# --- D/E financial exception (5 required scenarios) ---


def test_nonfinancial_low_de_passes(cfg):
    ok, _ = row_passes_filters(
        _row(sector="Industrials", de=0.5),
        [{"metric": "debt_to_equity", "operator": "lte", "value": 1.0}],
        cfg,
    )
    assert ok is True


def test_nonfinancial_high_de_fails(cfg):
    ok, failed = row_passes_filters(
        _row(sector="Industrials", de=2.5),
        [{"metric": "debt_to_equity", "operator": "lte", "value": 1.0}],
        cfg,
    )
    assert ok is False
    assert failed == ["debt_to_equity"]


def test_financial_high_de_waived(cfg):
    """Core exception: Financials skip the D/E filter even with high leverage."""
    ok, _ = row_passes_filters(
        _row(sector="Financials", de=8.25),
        [{"metric": "debt_to_equity", "operator": "lte", "value": 1.0}],
        cfg,
    )
    assert ok is True


def test_financial_missing_de_waived(cfg):
    """Waiver holds for missing D/E too (configured policy, not an accident)."""
    ok, _ = row_passes_filters(
        _row(sector="Financials", de=None),
        [{"metric": "debt_to_equity", "operator": "lte", "value": 1.0}],
        cfg,
    )
    assert ok is True


def test_sector_mapping_is_config_driven(cfg):
    excluded = cfg["exceptions"]["debt_to_equity"]["excluded_sectors"]
    assert "Financials" in excluded  # exact DB label present
    # Case-insensitive matching, not a hard-coded `== "Bank"` branch.
    assert is_financial_sector("financials", excluded) is True
    assert is_financial_sector("FINANCIALS", excluded) is True
    assert is_financial_sector("Industrials", excluded) is False
    assert is_financial_sector(None, excluded) is False


def test_de_waiver_can_be_disabled_per_filter(cfg):
    """Debt-free preset opts out: financials must satisfy D/E too."""
    flt = {"metric": "debt_to_equity", "operator": "lte", "value": 0.1,
           "apply_exception": False}
    assert should_waive_de_filter("Financials", cfg, flt) is False
    ok, _ = row_passes_filters(_row(sector="Financials", de=6.8), [flt], cfg)
    assert ok is False
    ok, _ = row_passes_filters(_row(sector="Financials", de=0.001), [flt], cfg)
    assert ok is True


# --- ICR edge cases ---


def test_icr_normal(cfg):
    # EBIT 100 / interest 10 -> 10 (Sprint 2 formula behaviour)
    assert effective_interest_coverage(_row(icr=10.0, debt=500, interest=10.0), cfg) == 10.0


def test_icr_debtfree_zero_interest_is_inf(cfg):
    """Case A: Debt=0, Interest=0 -> +inf (passes any positive threshold)."""
    eff = effective_interest_coverage(_row(icr=None, debt=0.0, interest=0.0), cfg)
    assert eff == math.inf
    ok, _ = row_passes_filters(
        _row(icr=None, debt=0.0, interest=0.0),
        [{"metric": "interest_coverage_ratio", "operator": "gte", "value": 3}],
        cfg,
    )
    assert ok is True


def test_icr_debtfree_with_interest_uses_normal_icr(cfg):
    """Case B: Debt=0 but Interest>0 -> normal ICR, NOT automatic inf."""
    eff = effective_interest_coverage(_row(icr=198.8, debt=0.0, interest=10.0), cfg)
    assert eff == pytest.approx(198.8)
    ok, _ = row_passes_filters(
        _row(icr=2.0, debt=0.0, interest=50.0),
        [{"metric": "interest_coverage_ratio", "operator": "gte", "value": 10}],
        cfg,
    )
    assert ok is False


def test_icr_zero_interest_no_crash(cfg):
    eff = effective_interest_coverage(_row(icr=None, debt=500.0, interest=0.0), cfg)
    assert eff == math.inf  # no ZeroDivisionError


def test_icr_missing_interest_fails(cfg):
    """Case E: missing interest -> missing -> filter fails (never inferred)."""
    eff = effective_interest_coverage(_row(icr=10.0, debt=100.0, interest=None), cfg)
    assert eff is None
    ok, _ = row_passes_filters(
        _row(icr=10.0, debt=100.0, interest=None),
        [{"metric": "interest_coverage_ratio", "operator": "gte", "value": 3}],
        cfg,
    )
    assert ok is False


def test_icr_negative_interest_policy(cfg):
    """Case D: negative interest follows configured policy (inf), not silent 0."""
    eff = effective_interest_coverage(_row(icr=5.0, debt=100.0, interest=-20.0), cfg)
    assert eff == math.inf


def test_debt_free_detection_prefers_debt_over_ratio():
    assert is_debt_free(0.0) is True
    assert is_debt_free(0) is True
    assert is_debt_free(63.0) is False
    # NULL debt is NEVER debt-free (even if the displayed D/E is 0.0).
    assert is_debt_free(None) is False
    assert is_debt_free(float("nan")) is False
