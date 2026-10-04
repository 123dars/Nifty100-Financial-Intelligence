import logging

logger = logging.getLogger(__name__)

def net_profit_margin(net_profit, sales):
    if not sales or sales == 0 or net_profit is None:
        return None
    return (net_profit / sales) * 100

def operating_profit_margin(operating_profit, sales, db_opm_percentage=None):
    if not sales or sales == 0 or operating_profit is None:
        return None
    computed_opm = (operating_profit / sales) * 100
    if db_opm_percentage is not None:
        if abs(computed_opm - db_opm_percentage) > 1.0:
            logger.warning(f"OPM mismatch: computed {computed_opm}, db has {db_opm_percentage}")
    return computed_opm

def return_on_equity(net_profit, equity_capital, reserves):
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0 or net_profit is None:
        return None
    return (net_profit / equity) * 100

def return_on_capital_employed(ebit, equity, reserves, borrowings):
    capital_employed = (equity or 0) + (reserves or 0) + (borrowings or 0)
    if capital_employed == 0 or ebit is None:
        return None
    return (ebit / capital_employed) * 100

def return_on_assets(net_profit, total_assets):
    if not total_assets or total_assets == 0 or net_profit is None:
        return None
    return (net_profit / total_assets) * 100

def debt_to_equity(borrowings, equity_capital, reserves, is_financials=False):
    borrowings = borrowings or 0
    equity = (equity_capital or 0) + (reserves or 0)
    
    if borrowings == 0:
        de = 0.0
    elif equity <= 0:
        de = None
    else:
        de = borrowings / equity
        
    high_leverage_flag = False
    if de is not None and de > 5 and not is_financials:
        high_leverage_flag = True
        
    return de, high_leverage_flag

def interest_coverage_ratio(operating_profit, other_income, interest):
    ebit = (operating_profit or 0) + (other_income or 0)
    if not interest or interest == 0:
        return None, "Debt Free", False
    
    icr = ebit / interest
    icr_label = None
    icr_warning_flag = False
    if icr < 1.5:
        icr_warning_flag = True
        
    return icr, icr_label, icr_warning_flag

def net_debt(borrowings, investments):
    return (borrowings or 0) - (investments or 0)

def asset_turnover(sales, total_assets):
    if not total_assets or total_assets == 0:
        return None
    return (sales or 0) / total_assets
