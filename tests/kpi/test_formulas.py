import pytest
import logging
from src.analytics.ratios import *
from src.analytics.cagr import *
from src.analytics.cashflow_kpis import *

def test_net_profit_margin_normal():
    assert net_profit_margin(100, 1000) == 10.0

def test_net_profit_margin_zero_denominator():
    assert net_profit_margin(100, 0) is None
    assert net_profit_margin(100, None) is None

def test_operating_profit_margin_mismatch(caplog):
    with caplog.at_level(logging.WARNING):
        res = operating_profit_margin(150, 1000, db_opm_percentage=10.0)
        assert res == 15.0
        assert "OPM mismatch" in caplog.text

def test_operating_profit_margin_normal():
    res = operating_profit_margin(100, 1000, db_opm_percentage=10.0)
    assert res == 10.0

def test_return_on_equity_normal():
    assert return_on_equity(100, 400, 100) == 20.0

def test_return_on_equity_negative_equity():
    assert return_on_equity(100, -100, -50) is None

def test_return_on_assets_normal():
    assert return_on_assets(100, 2000) == 5.0

def test_return_on_assets_zero():
    assert return_on_assets(100, 0) is None

def test_debt_to_equity_debt_free():
    de, flag = debt_to_equity(0, 500, 500)
    assert de == 0.0
    assert not flag

def test_debt_to_equity_high_flag():
    de, flag = debt_to_equity(6000, 500, 500)
    assert de == 6.0
    assert flag is True

def test_debt_to_equity_financials():
    de, flag = debt_to_equity(6000, 500, 500, is_financials=True)
    assert de == 6.0
    assert flag is False

def test_interest_coverage_zero_interest():
    icr, label, flag = interest_coverage_ratio(500, 100, 0)
    assert icr is None
    assert label == "Debt Free"
    assert not flag

def test_interest_coverage_normal():
    icr, label, flag = interest_coverage_ratio(500, 100, 300)
    assert icr == 2.0
    assert label is None
    assert not flag

def test_interest_coverage_warning():
    icr, label, flag = interest_coverage_ratio(100, 0, 100)
    assert icr == 1.0
    assert flag is True

def test_asset_turnover():
    assert asset_turnover(1000, 2000) == 0.5
    assert asset_turnover(1000, 0) is None

def test_cagr_normal():
    cagr, flag = calculate_cagr(100, 133.1, 3)
    assert round(cagr, 1) == 10.0
    assert flag == "NORMAL"

def test_cagr_turnaround():
    cagr, flag = calculate_cagr(-50, 100, 3)
    assert cagr is None
    assert flag == "TURNAROUND"

def test_cagr_decline_to_loss():
    cagr, flag = calculate_cagr(100, -50, 3)
    assert cagr is None
    assert flag == "DECLINE_TO_LOSS"

def test_cagr_both_negative():
    cagr, flag = calculate_cagr(-50, -100, 3)
    assert cagr is None
    assert flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    cagr, flag = calculate_cagr(0, 100, 3)
    assert cagr is None
    assert flag == "ZERO_BASE"

def test_cagr_insufficient():
    cagr, flag = calculate_cagr(100, 200, 0)
    assert cagr is None
    assert flag == "INSUFFICIENT"
    
def test_free_cash_flow():
    assert free_cash_flow(500, -200) == 300
    
def test_cfo_quality_score():
    score, label = cfo_quality_score([1.2, 1.1, 1.3])
    assert label == "High Quality"

def test_capex_intensity():
    intensity, label = capex_intensity(-50, 1000)
    assert intensity == 5.0
    assert label == "Moderate"

def test_fcf_conversion():
    assert fcf_conversion_rate(300, 600) == 50.0

def test_capital_allocation():
    pattern, label = capital_allocation_pattern(500, -200, -100, 1.5)
    assert label == "Shareholder Returns"
