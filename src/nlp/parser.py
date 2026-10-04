import pandas as pd
import sqlite3
import re
import os

def main():
    # Setup paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, 'nifty100.db')
    analysis_path = os.path.join(base_dir, 'data', 'analysis.xlsx')
    output_parsed = os.path.join(base_dir, 'output', 'analysis_parsed.csv')
    output_failures = os.path.join(base_dir, 'output', 'parse_failures.csv')
    output_divergence = os.path.join(base_dir, 'output', 'cagr_divergence.csv')

    # Load data
    df = pd.read_excel(analysis_path, skiprows=1)
    
    # Load companies mapping
    conn = sqlite3.connect(db_path)
    companies = pd.read_sql_query("SELECT company_id, ticker FROM companies", conn)
    ticker_to_id = dict(zip(companies['ticker'], companies['company_id']))

    # Target fields
    target_fields = ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe']
    
    # Regex
    pattern = re.compile(r'(\d+)\s*Years?:?\s*([\d.-]+)%')

    parsed_records = []
    failures = []

    for _, row in df.iterrows():
        ticker = str(row['company_id']).strip()
        comp_id = ticker_to_id.get(ticker)
        if not comp_id:
            continue
            
        for field in target_fields:
            if field in row and pd.notna(row[field]):
                text = str(row[field]).strip()
                # Text could be multiline like: "10 Years: 15%\n5 Years: 8%"
                # Split by newline or findall
                matches = pattern.findall(text)
                if matches:
                    for match in matches:
                        period = int(match[0])
                        val = float(match[1])
                        parsed_records.append({
                            'company_id': comp_id,
                            'metric_type': field,
                            'period_years': period,
                            'value_pct': val
                        })
                else:
                    failures.append({
                        'company_id': comp_id,
                        'ticker': ticker,
                        'metric_type': field,
                        'text': text
                    })

    # Save parsed records
    parsed_df = pd.DataFrame(parsed_records)
    parsed_df.to_csv(output_parsed, index=False)
    
    # Save failures
    fail_df = pd.DataFrame(failures)
    fail_df.to_csv(output_failures, index=False)
    
    # Cross-validation against Ratio Engine
    # Get computed CAGR (we'll use year 2024 or max year per company)
    ratios = pd.read_sql_query("""
        SELECT company_id, year, revenue_cagr_5yr, pat_cagr_5yr 
        FROM financial_ratios 
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    
    divergence_records = []
    
    for _, parsed in parsed_df.iterrows():
        if parsed['period_years'] == 5:
            metric = parsed['metric_type']
            c_id = parsed['company_id']
            val = parsed['value_pct']
            
            # Find in ratios
            ratio_row = ratios[ratios['company_id'] == c_id]
            if not ratio_row.empty:
                comp_val = None
                if metric == 'compounded_sales_growth':
                    comp_val = ratio_row.iloc[0]['revenue_cagr_5yr']
                elif metric == 'compounded_profit_growth':
                    comp_val = ratio_row.iloc[0]['pat_cagr_5yr']
                
                if comp_val is not None and pd.notna(comp_val):
                    # check divergence > 5%
                    # is it absolute > 5 or relative > 5%?
                    # "flag divergence > 5%". Usually means absolute difference > 5% or relative > 5%.
                    # Let's use absolute diff > 5 as value is in %, meaning 15% vs 10%
                    if abs(comp_val - val) > 5.0:
                        divergence_records.append({
                            'company_id': c_id,
                            'metric': metric,
                            'parsed_value': val,
                            'computed_value': comp_val,
                            'divergence': abs(comp_val - val)
                        })
    
    div_df = pd.DataFrame(divergence_records)
    div_df.to_csv(output_divergence, index=False)
    
    conn.close()

if __name__ == '__main__':
    main()
