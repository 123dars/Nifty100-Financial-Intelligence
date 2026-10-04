import sqlite3
import pandas as pd
import numpy as np
import os
from pathlib import Path

def run_valuation():
    db_path = 'nifty100.db'
    conn = sqlite3.connect(db_path)
    
    # Get latest year data
    query = """
    SELECT 
        c.company_id, c.company_name, c.sector,
        f.year,
        f.free_cash_flow_cr as fcf,
        s.pe_ratio, s.pb_ratio,
        p.profit_before_tax, p.interest, p.depreciation,
        b.borrowings, b.cash
    FROM companies c
    JOIN financial_ratios f ON c.company_id = f.company_id
    LEFT JOIN financial_ratios_source s ON f.company_id = s.company_id AND f.year = s.year
    LEFT JOIN profitandloss p ON c.company_id = p.company_id AND f.year = p.year
    LEFT JOIN balancesheet b ON c.company_id = b.company_id AND f.year = b.year
    """
    df = pd.read_sql_query(query, conn)
    latest_year = df['year'].max()
    df_latest = df[df['year'] == latest_year].copy()
    
    # 5yr median PE
    query_pe = """
    SELECT company_id, pe_ratio FROM financial_ratios_source WHERE year >= ?
    """
    df_pe_history = pd.read_sql_query(query_pe, conn, params=[latest_year - 4])
    conn.close()
    
    median_pe_5yr = df_pe_history.groupby('company_id')['pe_ratio'].median().reset_index()
    median_pe_5yr.rename(columns={'pe_ratio': '5yr_median_PE'}, inplace=True)
    
    df_latest = df_latest.merge(median_pe_5yr, on='company_id', how='left')
    
    # Load market cap
    if not os.path.exists('data/market_cap.xlsx'):
        print("data/market_cap.xlsx not found.")
        return
        
    mc = pd.read_excel('data/market_cap.xlsx')
    df_latest = df_latest.merge(mc[['company_id', 'market_cap_crore']], on='company_id', how='left')
    
    # Convert types
    for c in ['fcf', 'pe_ratio', 'pb_ratio', 'profit_before_tax', 'interest', 'depreciation', 'borrowings', 'cash', 'market_cap_crore']:
        df_latest[c] = pd.to_numeric(df_latest[c], errors='coerce')
        
    # FCF Yield
    df_latest['FCF_yield_pct'] = np.where(df_latest['market_cap_crore'] > 0, 
                                        df_latest['fcf'] / df_latest['market_cap_crore'] * 100, 
                                        np.nan)
                                        
    # EV / EBITDA
    ev = df_latest['market_cap_crore'].fillna(0) + df_latest['borrowings'].fillna(0) - df_latest['cash'].fillna(0)
    ebitda = df_latest['profit_before_tax'].fillna(0) + df_latest['interest'].fillna(0) + df_latest['depreciation'].fillna(0)
    df_latest['EV/EBITDA'] = np.where(ebitda > 0, ev / ebitda, np.nan)
    
    # Sector median PE
    sector_pe = df_latest.groupby('sector')['pe_ratio'].median().to_dict()
    df_latest['sector_median_PE'] = df_latest['sector'].map(sector_pe)
    
    # PE vs sector median pct
    df_latest['PE_vs_sector_median_pct'] = np.where(df_latest['sector_median_PE'] > 0,
                                                  (df_latest['pe_ratio'] / df_latest['sector_median_PE'] - 1) * 100,
                                                  np.nan)
                                                  
    # Flags
    def get_flag(row):
        pe = row['pe_ratio']
        sec_pe = row['sector_median_PE']
        if pd.isna(pe) or pd.isna(sec_pe):
            return 'Fair'
        if pe > sec_pe * 1.5:
            return 'Caution'
        if pe < sec_pe * 0.7:
            return 'Discount'
        return 'Fair'
        
    df_latest['flag'] = df_latest.apply(get_flag, axis=1)
    
    out_cols = ['company_id', 'company_name', 'sector', 'pe_ratio', 'pb_ratio', 'EV/EBITDA', 
                'FCF_yield_pct', '5yr_median_PE', 'PE_vs_sector_median_pct', 'flag']
                
    df_out = df_latest[out_cols].copy()
    df_out.rename(columns={'pe_ratio': 'P/E', 'pb_ratio': 'P/B'}, inplace=True)
    
    os.makedirs('output', exist_ok=True)
    df_out.to_excel('output/valuation_summary.xlsx', index=False)
    
    df_flags = df_out[df_out['flag'].isin(['Caution', 'Discount'])].copy()
    df_flags.to_csv('output/valuation_flags.csv', index=False)
    
    print("Valuation module complete. Generated valuation_summary.xlsx and valuation_flags.csv.")

if __name__ == '__main__':
    run_valuation()
