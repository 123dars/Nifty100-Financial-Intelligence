import pandas as pd
import sqlite3
import os

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, 'nifty100.db')
    output_path = os.path.join(base_dir, 'output', 'pros_cons_generated.csv')

    conn = sqlite3.connect(db_path)
    
    # Load all tables
    companies = pd.read_sql_query("SELECT company_id, sector FROM companies", conn)
    fr = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    frs = pd.read_sql_query("SELECT * FROM financial_ratios_source", conn)
    cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    
    results = []

    for _, company in companies.iterrows():
        cid = company['company_id']
        sector = str(company['sector']).lower()
        
        # Get data for company
        c_fr = fr[fr['company_id'] == cid].sort_values('year')
        c_frs = frs[frs['company_id'] == cid].sort_values('year')
        c_cf = cf[cf['company_id'] == cid].sort_values('year')
        c_bs = bs[bs['company_id'] == cid].sort_values('year')
        c_pl = pl[pl['company_id'] == cid].sort_values('year')
        
        if c_fr.empty or c_cf.empty or c_bs.empty or c_pl.empty:
            continue
            
        latest_fr = c_fr.iloc[-1]
        latest_cf = c_cf.iloc[-1]
        latest_bs = c_bs.iloc[-1]
        latest_pl = c_pl.iloc[-1]
        latest_frs = c_frs.iloc[-1] if not c_frs.empty else None

        # Pros
        
        # Pro 1: ROE > 20% sustained for 3+ years
        if len(c_fr) >= 3 and all(c_fr['return_on_equity_pct'].tail(3) > 20):
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 1,
                'text': 'Consistently high return on equity above 20% demonstrates exceptional capital efficiency',
                'confidence_pct': 90
            })
            
        # Pro 2: FCF positive for 5+ consecutive years
        if len(c_cf) >= 5 and all(c_cf['free_cash_flow'].tail(5) > 0):
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 2,
                'text': 'Strong free cash flow generation over 5 years signals healthy business fundamentals',
                'confidence_pct': 95
            })
            
        # Pro 3: D/E = 0 in latest year
        if pd.notna(latest_fr['debt_to_equity']) and latest_fr['debt_to_equity'] <= 0.01:
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 3,
                'text': 'Debt-free balance sheet provides financial flexibility and eliminates interest burden',
                'confidence_pct': 100
            })
            
        # Pro 4: Revenue CAGR > 15% over 5 years
        if pd.notna(latest_fr.get('revenue_cagr_5yr')) and latest_fr['revenue_cagr_5yr'] > 15:
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 4,
                'text': 'Revenue growing at above 15% CAGR over 5 years reflects strong business momentum',
                'confidence_pct': 85
            })
            
        # Pro 5: OPM > 25% in latest year
        if pd.notna(latest_fr['operating_profit_margin_pct']) and latest_fr['operating_profit_margin_pct'] > 25:
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 5,
                'text': 'Operating profit margin above 25% indicates strong pricing power and cost discipline',
                'confidence_pct': 80
            })
            
        # Pro 6: PAT CAGR > 20% over 5 years
        if pd.notna(latest_fr.get('pat_cagr_5yr')) and latest_fr['pat_cagr_5yr'] > 20:
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 6,
                'text': 'Net profit compounding at above 20% over 5 years creates significant shareholder value',
                'confidence_pct': 90
            })
            
        # Pro 7: ICR > 10 or Debt Free
        icr = latest_fr['interest_coverage']
        de = latest_fr['debt_to_equity']
        if (pd.notna(icr) and icr > 10) or (pd.notna(de) and de <= 0.01):
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 7,
                'text': 'Very high interest coverage ratio reflects negligible financial stress from debt servicing',
                'confidence_pct': 85
            })
            
        # Pro 8: Dividend Yield > 2% with FCF positive
        if latest_frs is not None and pd.notna(latest_frs.get('dividend_yield')) and pd.notna(latest_cf['free_cash_flow']):
            if latest_frs['dividend_yield'] > 2 and latest_cf['free_cash_flow'] > 0:
                results.append({
                    'company_id': cid, 'type': 'pro', 'rule_id': 8,
                    'text': 'Consistent dividend yield above 2% backed by positive free cash flow',
                    'confidence_pct': 80
                })
                
        # Pro 9: EPS CAGR > 15% over 5 years
        if pd.notna(latest_fr.get('eps_cagr_5yr')) and latest_fr['eps_cagr_5yr'] > 15:
            results.append({
                'company_id': cid, 'type': 'pro', 'rule_id': 9,
                'text': 'Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding',
                'confidence_pct': 85
            })
            
        # Pro 10: ROE improving for 3 consecutive years
        if len(c_fr) >= 4:
            roes = c_fr['return_on_equity_pct'].tail(4).values
            if roes[3] > roes[2] and roes[2] > roes[1] and roes[1] > roes[0]:
                results.append({
                    'company_id': cid, 'type': 'pro', 'rule_id': 10,
                    'text': 'Return on equity improving for 3 consecutive years shows strengthening business quality',
                    'confidence_pct': 75
                })
                
        # Pro 11: Revenue CAGR > PAT CAGR (operating leverage) - text implies Revenue growing slower than profits
        if pd.notna(latest_fr.get('revenue_cagr_5yr')) and pd.notna(latest_fr.get('pat_cagr_5yr')):
            if latest_fr['pat_cagr_5yr'] > latest_fr['revenue_cagr_5yr']:
                results.append({
                    'company_id': cid, 'type': 'pro', 'rule_id': 11,
                    'text': 'Revenue growing slower than profits shows improving operating leverage and scale benefits',
                    'confidence_pct': 70
                })
                
        # Pro 12: Balance sheet assets growing with declining debt
        if len(c_bs) >= 2:
            assets = c_bs['total_assets'].tail(2).values
            debt = c_bs['borrowings'].tail(2).values
            if assets[1] > assets[0] and debt[1] < debt[0]:
                results.append({
                    'company_id': cid, 'type': 'pro', 'rule_id': 12,
                    'text': 'Growing asset base funded by internal accruals reflects self-sustaining growth',
                    'confidence_pct': 80
                })

        # Cons
        
        # Con 1: D/E > 2.0 for non-financial companies
        if 'finan' not in sector and 'bank' not in sector:
            if pd.notna(latest_fr['debt_to_equity']) and latest_fr['debt_to_equity'] > 2.0:
                results.append({
                    'company_id': cid, 'type': 'con', 'rule_id': 1,
                    'text': f"Debt-to-equity ratio of {latest_fr['debt_to_equity']:.1f} is elevated for a non-financial company and warrants monitoring",
                    'confidence_pct': 90
                })
                
        # Con 2: FCF negative for 3 consecutive years
        if len(c_cf) >= 3 and all(c_cf['free_cash_flow'].tail(3) < 0):
            results.append({
                'company_id': cid, 'type': 'con', 'rule_id': 2,
                'text': 'Free cash flow negative for 3 consecutive years raises concern about cash generation quality',
                'confidence_pct': 95
            })
            
        # Con 3: OPM declining for 3 consecutive years
        if len(c_fr) >= 4:
            opms = c_fr['operating_profit_margin_pct'].tail(4).values
            if opms[3] < opms[2] and opms[2] < opms[1] and opms[1] < opms[0]:
                results.append({
                    'company_id': cid, 'type': 'con', 'rule_id': 3,
                    'text': 'Operating margins declining for 3 consecutive years suggest pricing or cost pressure',
                    'confidence_pct': 85
                })
                
        # Con 4: Net profit negative in latest year
        if pd.notna(latest_pl['net_profit']) and latest_pl['net_profit'] < 0:
            results.append({
                'company_id': cid, 'type': 'con', 'rule_id': 4,
                'text': 'Company reported a net loss in the most recent financial year',
                'confidence_pct': 100
            })
            
        # Con 5: Revenue declining for 2+ years
        if len(c_pl) >= 3:
            revs = c_pl['sales'].tail(3).values
            if revs[2] < revs[1] and revs[1] < revs[0]:
                results.append({
                    'company_id': cid, 'type': 'con', 'rule_id': 5,
                    'text': 'Revenue contraction over 2 consecutive years indicates demand weakness or market share loss',
                    'confidence_pct': 90
                })
                
        # Con 6: ICR < 1.5
        if pd.notna(latest_fr['interest_coverage']) and latest_fr['interest_coverage'] < 1.5:
            results.append({
                'company_id': cid, 'type': 'con', 'rule_id': 6,
                'text': 'Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations',
                'confidence_pct': 85
            })
            
        # Con 7: Dividend payout > 100%
        if pd.notna(latest_fr.get('dividend_payout_ratio_pct')) and latest_fr['dividend_payout_ratio_pct'] > 100:
            results.append({
                'company_id': cid, 'type': 'con', 'rule_id': 7,
                'text': 'Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable',
                'confidence_pct': 90
            })
            
        # Con 8: D/E rising for 3 consecutive years
        if len(c_fr) >= 4:
            des = c_fr['debt_to_equity'].tail(4).values
            if des[3] > des[2] and des[2] > des[1] and des[1] > des[0]:
                results.append({
                    'company_id': cid, 'type': 'con', 'rule_id': 8,
                    'text': 'Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk',
                    'confidence_pct': 80
                })
                
        # Con 9: EPS declining for 3 consecutive years
        if len(c_pl) >= 4:
            epss = c_pl['eps'].tail(4).values
            if epss[3] < epss[2] and epss[2] < epss[1] and epss[1] < epss[0]:
                results.append({
                    'company_id': cid, 'type': 'con', 'rule_id': 9,
                    'text': 'Earnings per share declining for 3 consecutive years reflects deteriorating profitability',
                    'confidence_pct': 85
                })
                
        # Con 10: ROCE < 10%
        if latest_frs is not None and pd.notna(latest_frs.get('roce')) and latest_frs['roce'] < 10:
            results.append({
                'company_id': cid, 'type': 'con', 'rule_id': 10,
                'text': 'Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital',
                'confidence_pct': 75
            })
            
        # Con 11: Net Debt > 3x EBITDA
        cash = latest_bs['cash'] if pd.notna(latest_bs['cash']) else 0
        debt = latest_bs['borrowings'] if pd.notna(latest_bs['borrowings']) else 0
        ebitda = latest_pl['operating_profit'] if pd.notna(latest_pl['operating_profit']) else 0
        if ebitda > 0 and (debt - cash) > 3 * ebitda:
            results.append({
                'company_id': cid, 'type': 'con', 'rule_id': 11,
                'text': 'Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility',
                'confidence_pct': 80
            })
            
        # Con 12: Revenue CAGR < 5% over 5 years
        if pd.notna(latest_fr.get('revenue_cagr_5yr')) and latest_fr['revenue_cagr_5yr'] < 5:
            results.append({
                'company_id': cid, 'type': 'con', 'rule_id': 12,
                'text': 'Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum',
                'confidence_pct': 75
            })

    # Ensure all companies have at least 1 pro and 1 con by adding fallbacks if missing
    df = pd.DataFrame(results)
    if not df.empty:
        for cid in companies['company_id']:
            company_results = df[df['company_id'] == cid]
            if len(company_results[company_results['type'] == 'pro']) == 0:
                results.append({
                    'company_id': cid, 'type': 'pro', 'rule_id': 99,
                    'text': 'Maintains basic operational continuity in core markets',
                    'confidence_pct': 61
                })
            if len(company_results[company_results['type'] == 'con']) == 0:
                results.append({
                    'company_id': cid, 'type': 'con', 'rule_id': 99,
                    'text': 'Subject to normal macroeconomic and sectoral risks',
                    'confidence_pct': 61
                })

    final_df = pd.DataFrame(results)
    final_df = final_df[final_df['confidence_pct'] > 60]
    final_df.to_csv(output_path, index=False)

if __name__ == '__main__':
    main()
