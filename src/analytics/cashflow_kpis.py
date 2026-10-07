import pandas as pd
import sqlite3
import os

def free_cash_flow(operating_cash_flow, investing_cash_flow):
    return (operating_cash_flow or 0) + (investing_cash_flow or 0)

def cfo_quality_score(cfo_pat_ratios):
    if not cfo_pat_ratios:
        return None, "INSUFFICIENT"
    avg_ratio = sum(cfo_pat_ratios) / len(cfo_pat_ratios)
    if avg_ratio > 1.0:
        return avg_ratio, "High Quality"
    elif 0.5 <= avg_ratio <= 1.0:
        return avg_ratio, "Moderate"
    else:
        return avg_ratio, "Accrual Risk"

def capex_intensity(investing_cash_flow, sales):
    if not sales or sales == 0:
        return None, None
    intensity = (abs(investing_cash_flow or 0) / sales) * 100
    if intensity < 3:
        label = "Asset Light"
    elif 3 <= intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return intensity, label

def fcf_conversion_rate(fcf, operating_profit):
    if not operating_profit or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100

def capital_allocation_pattern(cfo, cfi, cff, cfo_pat_ratio=None):
    cfo_sign = '+' if (cfo or 0) > 0 else '-'
    cfi_sign = '+' if (cfi or 0) > 0 else '-'
    cff_sign = '+' if (cff or 0) > 0 else '-'
    pattern_str = f"({cfo_sign}, {cfi_sign}, {cff_sign})"
    
    if pattern_str == "(+, -, -)":
        return "Shareholder Returns" if cfo_pat_ratio and cfo_pat_ratio > 1.0 else "Reinvestor"
    elif pattern_str == "(+, +, -)":
        return "Liquidating Assets"
    elif pattern_str == "(-, +, +)":
        return "Distress Signal"
    elif pattern_str == "(-, -, +)":
        return "Growth Funded by Debt"
    elif pattern_str == "(+, +, +)":
        return "Cash Accumulator"
    elif pattern_str == "(-, -, -)":
        return "Pre-Revenue"
    elif pattern_str == "(+, -, +)":
        return "Mixed"
    else:
        return "Unknown"

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, 'nifty100.db')
    output_cf = os.path.join(base_dir, 'output', 'cashflow_intelligence.xlsx')
    output_distress = os.path.join(base_dir, 'output', 'distress_alerts.csv')
    output_pattern = os.path.join(base_dir, 'output', 'pattern_changes.csv')

    conn = sqlite3.connect(db_path)
    
    companies = pd.read_sql_query("SELECT company_id, sector FROM companies", conn)
    cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
    pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    fr = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    
    results = []
    distress = []
    pattern_changes = []
    
    for _, company in companies.iterrows():
        cid = company['company_id']
        sector = company['sector']
        
        c_cf = cf[cf['company_id'] == cid].sort_values('year')
        c_pl = pl[pl['company_id'] == cid].sort_values('year')
        c_bs = bs[bs['company_id'] == cid].sort_values('year')
        c_fr = fr[fr['company_id'] == cid].sort_values('year')
        
        if c_cf.empty or c_pl.empty:
            continue
            
        latest_cf = c_cf.iloc[-1]
        latest_pl = c_pl.iloc[-1]
        
        # CFO Quality Score
        cfo_pat_ratios = []
        for i in range(max(0, len(c_cf)-5), len(c_cf)):
            row_cf = c_cf.iloc[i]
            row_pl_matches = c_pl[c_pl['year'] == row_cf['year']]
            if not row_pl_matches.empty:
                pat = row_pl_matches.iloc[0]['net_profit']
                if pd.notna(pat) and pat > 0 and pd.notna(row_cf['operating_cash_flow']):
                    cfo_pat_ratios.append(row_cf['operating_cash_flow'] / pat)
                    
        cfo_score, cfo_label = cfo_quality_score(cfo_pat_ratios)
        
        # CapEx Intensity
        sales = latest_pl['sales'] if pd.notna(latest_pl.get('sales')) else 0
        investing = latest_cf['investing_cash_flow']
        capex_pct, capex_label = capex_intensity(investing, sales)
        
        # Distress Signal
        cfo_val = latest_cf['operating_cash_flow']
        cff_val = latest_cf['financing_cash_flow']
        
        distress_flag = False
        if pd.notna(cfo_val) and cfo_val < 0 and pd.notna(cff_val) and cff_val > 0:
            distress_flag = True
            distress.append({
                'company_id': cid,
                'cfo': cfo_val,
                'cff': cff_val,
                'latest_net_profit': latest_pl['net_profit'] if 'net_profit' in latest_pl else None
            })
            
        # Deleveraging Flag
        deleveraging_flag = False
        if len(c_bs) >= 2:
            prev_bs = c_bs.iloc[-2]
            curr_bs = c_bs.iloc[-1]
            if pd.notna(cff_val) and cff_val < 0:
                if pd.notna(curr_bs.get('borrowings')) and pd.notna(prev_bs.get('borrowings')):
                    if curr_bs['borrowings'] < prev_bs['borrowings']:
                        deleveraging_flag = True
                        
        # FCF CAGR and Conversion
        fcf_cagr_5yr = c_fr.iloc[-1]['fcf_cagr_5yr'] if not c_fr.empty and 'fcf_cagr_5yr' in c_fr.columns else None
        
        latest_fcf = free_cash_flow(cfo_val, investing)
        op_profit = latest_pl['operating_profit'] if 'operating_profit' in latest_pl else 0
        fcf_conv = fcf_conversion_rate(latest_fcf, op_profit)
        
        # Capital Allocation Pattern
        cfo_pat_latest = cfo_val / latest_pl['net_profit'] if pd.notna(latest_pl.get('net_profit')) and latest_pl['net_profit'] > 0 else None
        cap_alloc_label = capital_allocation_pattern(cfo_val, investing, cff_val, cfo_pat_latest)
        
        # Year-over-year pattern change
        if len(c_cf) >= 2:
            prev_cf = c_cf.iloc[-2]
            prev_pl_matches = c_pl[c_pl['year'] == prev_cf['year']]
            prev_pat = prev_pl_matches.iloc[0]['net_profit'] if not prev_pl_matches.empty else 0
            prev_cfo_pat = prev_cf['operating_cash_flow'] / prev_pat if pd.notna(prev_pat) and prev_pat > 0 else None
            prev_cap_alloc = capital_allocation_pattern(prev_cf['operating_cash_flow'], prev_cf['investing_cash_flow'], prev_cf['financing_cash_flow'], prev_cfo_pat)
            
            if prev_cap_alloc != cap_alloc_label:
                pattern_changes.append({
                    'company_id': cid,
                    'year': latest_cf['year'],
                    'previous_pattern': prev_cap_alloc,
                    'current_pattern': cap_alloc_label
                })

        results.append({
            'company_id': cid,
            'sector': sector,
            'cfo_quality_score': cfo_score,
            'cfo_quality_label': cfo_label,
            'capex_intensity_pct': capex_pct,
            'capex_label': capex_label,
            'fcf_cagr_5yr': fcf_cagr_5yr,
            'fcf_conversion_pct': fcf_conv,
            'distress_flag': distress_flag,
            'deleveraging_flag': deleveraging_flag,
            'capital_allocation_label': cap_alloc_label
        })
        
    pd.DataFrame(results).to_excel(output_cf, index=False)
    pd.DataFrame(distress).to_csv(output_distress, index=False)
    pd.DataFrame(pattern_changes).to_csv(output_pattern, index=False)

if __name__ == '__main__':
    main()
