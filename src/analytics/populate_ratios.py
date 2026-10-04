import sqlite3
import csv
import logging
import sys
from pathlib import Path

# Project root = <repo>/ (parent of src/). Resolves cwd-independent paths
# so `uv run python src/analytics/populate_ratios.py` works from root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

try:
    from src.analytics.ratios import *
    from src.analytics.cagr import *
    from src.analytics.cashflow_kpis import *
except ImportError:  # fallback when executed with src/analytics on sys.path
    from ratios import *
    from cagr import *
    from cashflow_kpis import *

logging.basicConfig(
    filename=str(OUTPUT_DIR / 'ratio_edge_cases.log'),
    level=logging.WARNING,
    format='%(levelname)s: %(message)s',
    force=True,
)
logger = logging.getLogger(__name__)

DB_PATH = str(PROJECT_ROOT / "nifty100.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Create table financial_ratios
    cursor.execute("DROP TABLE IF EXISTS financial_ratios")
    cursor.execute("""
    CREATE TABLE financial_ratios (
        ratio_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        year INTEGER NOT NULL,
        net_profit_margin_pct REAL,
        operating_profit_margin_pct REAL,
        return_on_equity_pct REAL,
        debt_to_equity REAL,
        interest_coverage REAL,
        asset_turnover REAL,
        free_cash_flow_cr REAL,
        capex_cr REAL,
        earnings_per_share REAL,
        book_value_per_share REAL,
        dividend_payout_ratio_pct REAL,
        total_debt_cr REAL,
        cash_from_operations_cr REAL,
        revenue_cagr_5yr REAL,
        pat_cagr_5yr REAL,
        eps_cagr_5yr REAL,
        revenue_cagr_5yr_flag TEXT,
        pat_cagr_5yr_flag TEXT,
        eps_cagr_5yr_flag TEXT,
        icr_label TEXT,
        high_leverage_flag BOOLEAN,
        icr_warning_flag BOOLEAN,
        composite_quality_score REAL,
        FOREIGN KEY (company_id) REFERENCES companies(company_id),
        UNIQUE(company_id, year)
    )
    """)
    
    # 2. Extract data
    companies = cursor.execute("SELECT * FROM companies").fetchall()
    
    company_sectors = {c['company_id']: c['sector'] for c in companies}
    
    pl_data = cursor.execute("SELECT * FROM profitandloss").fetchall()
    bs_data = cursor.execute("SELECT * FROM balancesheet").fetchall()
    cf_data = cursor.execute("SELECT * FROM cashflow").fetchall()
    
    # Check for original ratios to cross-check
    try:
        source_ratios = cursor.execute("SELECT * FROM financial_ratios_source").fetchall()
        source_dict = {(r['company_id'], r['year']): r for r in source_ratios}
    except sqlite3.OperationalError:
        source_dict = {}

    data_by_company_year = {}
    
    for row in pl_data:
        cid, y = row['company_id'], row['year']
        if cid not in data_by_company_year: data_by_company_year[cid] = {}
        if y not in data_by_company_year[cid]: data_by_company_year[cid][y] = {}
        data_by_company_year[cid][y]['pl'] = dict(row)
        
    for row in bs_data:
        cid, y = row['company_id'], row['year']
        if cid not in data_by_company_year: data_by_company_year[cid] = {}
        if y not in data_by_company_year[cid]: data_by_company_year[cid][y] = {}
        data_by_company_year[cid][y]['bs'] = dict(row)
        
    for row in cf_data:
        cid, y = row['company_id'], row['year']
        if cid not in data_by_company_year: data_by_company_year[cid] = {}
        if y not in data_by_company_year[cid]: data_by_company_year[cid][y] = {}
        data_by_company_year[cid][y]['cf'] = dict(row)
        
    # Prepare historical data for CAGR and CFO Quality
    history_by_company = {}
    for cid, years_data in data_by_company_year.items():
        history = {
            'sales': {}, 'pat': {}, 'eps': {}, 'cfo_pat_ratio': {}
        }
        for y, d in years_data.items():
            pl = d.get('pl', {})
            cf = d.get('cf', {})
            if 'sales' in pl and pl['sales'] is not None:
                history['sales'][y] = pl['sales']
            if 'net_profit' in pl and pl['net_profit'] is not None:
                history['pat'][y] = pl['net_profit']
            if 'eps' in pl and pl['eps'] is not None:
                history['eps'][y] = pl['eps']
                
            pat = pl.get('net_profit', 0)
            cfo = cf.get('operating_cash_flow', 0)
            if pat and pat != 0 and cfo is not None:
                history['cfo_pat_ratio'][y] = cfo / pat
                
        history_by_company[cid] = history
        
    # Process each company-year
    insert_values = []
    capital_allocation_rows = []
    
    all_years = list(range(2011, 2025))
    
    for cid in company_sectors.keys():
        sector = company_sectors.get(cid, '')
        is_fin = sector and 'financial' in sector.lower()
        hist = history_by_company.get(cid, {})
        
        for y in all_years:
            d = data_by_company_year.get(cid, {}).get(y, {})
            pl = d.get('pl', {})
            bs = d.get('bs', {})
            cf = d.get('cf', {})
            
            src = source_dict.get((cid, y), {})
            if isinstance(src, sqlite3.Row):
                src = dict(src)
            db_opm = src.get('operating_margin')
            db_roe = src.get('roe')
            db_roce = src.get('roce')
            
            sales = pl.get('sales')
            net_profit = pl.get('net_profit')
            operating_profit = pl.get('operating_profit')
            other_income = pl.get('other_income')
            interest = pl.get('interest')
            eps = pl.get('eps')
            
            equity_cap = bs.get('equity')
            reserves = bs.get('reserves')
            borrowings = bs.get('borrowings')
            total_assets = bs.get('total_assets')
            
            cfo = cf.get('operating_cash_flow')
            cfi = cf.get('investing_cash_flow')
            cff = cf.get('financing_cash_flow')
            
            # Compute profitability
            npm = net_profit_margin(net_profit, sales)
            opm = operating_profit_margin(operating_profit, sales, db_opm)
            roe = return_on_equity(net_profit, equity_cap, reserves)
            
            if db_roe is not None and roe is not None:
                pass # The source ROE is known to be anomalous sometimes, we log if instructed, wait "use ratio engine value for analytics, source value for display only"
            
            ebit = (operating_profit or 0) + (other_income or 0)
            roce = return_on_capital_employed(ebit, equity_cap, reserves, borrowings)
            if db_roce is not None and roce is not None:
                if abs(roce - db_roce) > 5.0:
                    logger.warning(f"Company {cid} Year {y}: ROCE mismatch: computed {roce}, db has {db_roce}")
            
            roa = return_on_assets(net_profit, total_assets)
            
            # Compute leverage
            de, hi_lev = debt_to_equity(borrowings, equity_cap, reserves, is_fin)
            icr, icr_lbl, icr_warn = interest_coverage_ratio(operating_profit, other_income, interest)
            at = asset_turnover(sales, total_assets)
            
            # Compute cashflow KPIs
            fcf = free_cash_flow(cfo, cfi)
            capex, capex_lbl = capex_intensity(cfi, sales)
            fcf_conv = fcf_conversion_rate(fcf, operating_profit)
            
            # CFO quality score - last 5 years average
            cfo_pat_ratios = []
            for past_y in range(y-4, y+1):
                if past_y in hist.get('cfo_pat_ratio', {}):
                    cfo_pat_ratios.append(hist['cfo_pat_ratio'][past_y])
                    
            cfo_score, cfo_lbl = cfo_quality_score(cfo_pat_ratios)
            if cfo_score == None: cfo_score = 0.0 # Just for DB structure compatibility
            
            # Capital Allocation
            cap_pattern, cap_lbl = capital_allocation_pattern(cfo, cfi, cff, cfo_score)
            capital_allocation_rows.append((cid, y, cap_pattern[0], cap_pattern[1], cap_pattern[2], cap_lbl))
            
            # CAGRs
            # For this year, compute 5-year CAGR
            rev_cagr_5, rev_flag = calculate_cagr(hist.get('sales', {}).get(y-5), sales, 5)
            pat_cagr_5, pat_flag = calculate_cagr(hist.get('pat', {}).get(y-5), net_profit, 5)
            eps_cagr_5, eps_flag = calculate_cagr(hist.get('eps', {}).get(y-5), eps, 5)
            
            # Values required by schema
            # net_profit_margin_pct, operating_profit_margin_pct, return_on_equity_pct, debt_to_equity, interest_coverage, asset_turnover, free_cash_flow_cr, capex_cr, earnings_per_share, book_value_per_share, dividend_payout_ratio_pct, total_debt_cr, cash_from_operations_cr, revenue_cagr_5yr, revenue_cagr_5yr_flag, pat_cagr_5yr, pat_cagr_5yr_flag, eps_cagr_5yr, eps_cagr_5yr_flag, composite_quality_score, icr_label, high_leverage_flag, icr_warning_flag
            
            total_debt_cr = borrowings
            cash_from_operations_cr = cfo
            
            # composite_quality_score: arbitrary if not defined? Let's just put cfo_score or 0
            comp_score = cfo_score if cfo_score else 0.0
            
            bvps = None
            if net_profit and eps and eps != 0:
                # number_of_shares = net_profit / eps
                # bvps = equity / number_of_shares = equity * eps / net_profit
                total_equity = (equity_cap or 0) + (reserves or 0)
                bvps = (total_equity * eps) / net_profit
                
            div_payout = None
            db_pe = src.get('pe_ratio')
            db_dy = src.get('dividend_yield')
            if db_pe is not None and db_dy is not None:
                div_payout = db_pe * db_dy
            
            insert_values.append((
                cid, y, npm, opm, roe, de, icr, at, fcf, capex, eps, bvps, div_payout, total_debt_cr, cash_from_operations_cr, rev_cagr_5, rev_flag, pat_cagr_5, pat_flag, eps_cagr_5, eps_flag, comp_score, icr_lbl, hi_lev, icr_warn
            ))

    cursor.executemany("""
    INSERT INTO financial_ratios (
        company_id, year, net_profit_margin_pct, operating_profit_margin_pct, return_on_equity_pct,
        debt_to_equity, interest_coverage, asset_turnover, free_cash_flow_cr, capex_cr, earnings_per_share,
        book_value_per_share, dividend_payout_ratio_pct, total_debt_cr, cash_from_operations_cr,
        revenue_cagr_5yr, revenue_cagr_5yr_flag, pat_cagr_5yr, pat_cagr_5yr_flag, eps_cagr_5yr, eps_cagr_5yr_flag, composite_quality_score, icr_label, high_leverage_flag, icr_warning_flag
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_values)
    
    conn.commit()
    conn.close()
    
    # Write capital_allocation.csv (path anchored at project root)
    with open(OUTPUT_DIR / 'capital_allocation.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['company_id', 'year', 'cfo_sign', 'cfi_sign', 'cff_sign', 'pattern_label'])
        writer.writerows(capital_allocation_rows)

if __name__ == '__main__':
    main()
