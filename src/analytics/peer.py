import xlsxwriter
import sqlite3
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

def compute_percentiles():
    db_path = 'nifty100.db'
    conn = sqlite3.connect(db_path)
    
    # 1. Load data
    query = """
    SELECT 
        c.company_id, c.ticker, c.company_name, c.sector,
        f.year,
        f.return_on_equity_pct as roe,
        f.net_profit_margin_pct as npm,
        f.debt_to_equity as de,
        f.interest_coverage as icr,
        f.revenue_cagr_5yr as rev_cagr,
        f.pat_cagr_5yr as pat_cagr,
        f.eps_cagr_5yr as eps_cagr,
        f.asset_turnover as at,
        f.free_cash_flow_cr as fcf,
        p.operating_profit, p.other_income, p.net_profit, p.sales,
        b.equity, b.reserves, b.borrowings,
        f.composite_quality_score as composite_score
    FROM companies c
    JOIN financial_ratios f ON c.company_id = f.company_id
    LEFT JOIN profitandloss p ON c.company_id = p.company_id AND f.year = p.year
    LEFT JOIN balancesheet b ON c.company_id = b.company_id AND f.year = b.year
    """
    df = pd.read_sql(query, conn)
    
    latest_year = df['year'].max()
    df = df[df['year'] == latest_year].copy()
    
    for col in ['operating_profit', 'other_income', 'equity', 'reserves', 'borrowings']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    ebit = df['operating_profit'].fillna(0) + df['other_income'].fillna(0)
    ce = df['equity'].fillna(0) + df['reserves'].fillna(0) + df['borrowings'].fillna(0)
    df['roce'] = np.where(ce > 0, ebit / ce * 100, np.nan)
    
    # Read peer groups
    if os.path.exists('data/peer_groups.xlsx'):
        peers = pd.read_excel('data/peer_groups.xlsx')
        df = df.merge(peers[['company_id', 'peer_group_name']], on='company_id', how='left')
    else:
        df['peer_group_name'] = None
        
    metrics_map = {
        'ROE': 'roe',
        'ROCE': 'roce',
        'Net Profit Margin': 'npm',
        'D/E': 'de',
        'FCF': 'fcf',
        'PAT CAGR 5yr': 'pat_cagr',
        'Revenue CAGR 5yr': 'rev_cagr',
        'EPS CAGR 5yr': 'eps_cagr',
        'Interest Coverage': 'icr',
        'Asset Turnover': 'at'
    }
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            company_id INTEGER,
            peer_group_name TEXT,
            metric TEXT,
            value REAL,
            percentile_rank REAL,
            year INTEGER
        )
    ''')
    conn.execute('DELETE FROM peer_percentiles WHERE year = ?', (int(latest_year),))
    
    percentile_records = []
    
    for idx, row in df.iterrows():
        if pd.isna(row['peer_group_name']):
            print(f"Company {row['ticker']}: No peer group assigned")
    
    df_result = df.copy()
    
    for m_label, col in metrics_map.items():
        df_result[f'{col}_pct_rank'] = np.nan
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    for pg, group in df.groupby('peer_group_name'):
        for m_label, col in metrics_map.items():
            vals = group[col].dropna()
            if vals.empty:
                continue
            ranks = vals.rank(pct=True)
            if m_label == 'D/E':
                ranks = 1.0 - ranks
                
            for i, val in ranks.items():
                df_result.loc[i, f'{col}_pct_rank'] = val
                percentile_records.append((
                    int(df_result.loc[i, 'company_id']),
                    pg,
                    m_label,
                    float(df_result.loc[i, col]),
                    float(val),
                    int(latest_year)
                ))
                
    conn.executemany(
        'INSERT INTO peer_percentiles VALUES (?,?,?,?,?,?)',
        percentile_records
    )
    conn.commit()
    conn.close()
    
    return df_result, latest_year

def generate_radar_charts(df):
    os.makedirs('reports/radar_charts', exist_ok=True)
    
    radar_axes = {
        'ROE': 'roe',
        'ROCE': 'roce',
        'NPM': 'npm',
        'D/E': 'de',
        'FCF score': 'fcf', # Using FCF raw value scaled or pct rank? Chart says 8-axis, 0-100 scale best.
        'PAT CAGR 5yr': 'pat_cagr',
        'Revenue CAGR 5yr': 'rev_cagr',
        'Composite Score': 'composite_score'
    }
    
    # Scale all metrics to 0-1 for radar chart
    df_scaled = df.copy()
    for label, col in radar_axes.items():
        vals = pd.to_numeric(df_scaled[col], errors='coerce')
        if col == 'de':
            # Inverse
            vmin, vmax = vals.min(), vals.max()
            if vmax > vmin:
                df_scaled[col] = 1 - (vals - vmin) / (vmax - vmin)
            else:
                df_scaled[col] = 0.5
        else:
            vmin, vmax = vals.min(), vals.max()
            if vmax > vmin:
                df_scaled[col] = (vals - vmin) / (vmax - vmin)
            else:
                df_scaled[col] = 0.5
                
        df_scaled[col] = df_scaled[col].fillna(0)
        
    nifty_avg = df_scaled[[col for col in radar_axes.values()]].mean()
    
    labels = list(radar_axes.keys())
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
    
    for idx, row in df_scaled.iterrows():
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        
        values = row[[col for col in radar_axes.values()]].tolist()
        values += values[:1]
        
        ax.plot(angles, values, color='blue', linewidth=2)
        ax.fill(angles, values, color='blue', alpha=0.25)
        
        pg = row['peer_group_name']
        if pd.isna(pg):
            peer_avg = nifty_avg.tolist()
            peer_avg += peer_avg[:1]
            ax.plot(angles, peer_avg, color='grey', linewidth=2, linestyle='--')
            ax.set_title(f"{row['company_name']} (Nifty 100 Avg)")
        else:
            pg_avg = df_scaled[df_scaled['peer_group_name'] == pg][[col for col in radar_axes.values()]].mean().tolist()
            pg_avg += pg_avg[:1]
            ax.plot(angles, pg_avg, color='grey', linewidth=2, linestyle='--')
            ax.set_title(f"{row['company_name']} ({pg} Avg)")
            
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=8)
        ax.set_yticks([])
        
        plt.savefig(f"reports/radar_charts/{row['ticker']}_radar.png", dpi=150, bbox_inches='tight')
        plt.close()

def generate_peer_comparison_excel(df):
    os.makedirs('output', exist_ok=True)
    
    writer = pd.ExcelWriter('output/peer_comparison.xlsx', engine='xlsxwriter')
    workbook = writer.book
    
    green_format = workbook.add_format({'bg_color': '#C6EFCE'})
    yellow_format = workbook.add_format({'bg_color': '#FFEB9C'})
    red_format = workbook.add_format({'bg_color': '#FFC7CE'})
    gold_format = workbook.add_format({'bg_color': '#FFD700', 'bold': True})
    
    metrics_map = {
        'ROE': 'roe',
        'ROCE': 'roce',
        'Net Profit Margin': 'npm',
        'D/E': 'de',
        'FCF': 'fcf',
        'PAT CAGR 5yr': 'pat_cagr',
        'Revenue CAGR 5yr': 'rev_cagr',
        'EPS CAGR 5yr': 'eps_cagr',
        'Interest Coverage': 'icr',
        'Asset Turnover': 'at'
    }
    
    for pg, group in df.groupby('peer_group_name'):
        sheet_name = str(pg)[:31]
        
        cols_to_export = ['company_id', 'company_name', 'composite_score']
        for label, col in metrics_map.items():
            cols_to_export.extend([col, f'{col}_pct_rank'])
            
        df_pg = group[cols_to_export].copy()
        
        # Benchmark company = highest composite score
        if 'composite_score' in df_pg.columns and not df_pg['composite_score'].isna().all():
            benchmark_id = df_pg.loc[df_pg['composite_score'].idxmax(), 'company_id']
        else:
            benchmark_id = None
            
        # Add median row
        median_row = {'company_id': 'MEDIAN', 'company_name': 'Peer Group Median'}
        for label, col in metrics_map.items():
            median_row[col] = df_pg[col].median()
            median_row[f'{col}_pct_rank'] = np.nan
        median_row['composite_score'] = df_pg['composite_score'].median()
        
        df_pg = pd.concat([df_pg, pd.DataFrame([median_row])], ignore_index=True)
        df_pg.to_excel(writer, sheet_name=sheet_name, index=False)
        
        worksheet = writer.sheets[sheet_name]
        
        # Format benchmark row
        if benchmark_id is not None:
            # find row index (excel is 1-indexed, +1 for header)
            row_idx = df_pg[df_pg['company_id'] == benchmark_id].index[0] + 1
            worksheet.set_row(row_idx, None, gold_format)
            
        # Color code percentiles
        for label, col in metrics_map.items():
            pct_col = f'{col}_pct_rank'
            if pct_col in df_pg.columns:
                col_idx = df_pg.columns.get_loc(pct_col)
                col_letter = xlsxwriter.utility.xl_col_to_name(col_idx)
                
                # >= 0.75 green
                worksheet.conditional_format(f'{col_letter}2:{col_letter}{len(df_pg)}', {
                    'type': 'cell', 'criteria': '>=', 'value': 0.75, 'format': green_format
                })
                # 25-75 yellow
                worksheet.conditional_format(f'{col_letter}2:{col_letter}{len(df_pg)}', {
                    'type': 'cell', 'criteria': 'between', 'minimum': 0.25, 'maximum': 0.7499, 'format': yellow_format
                })
                # <= 0.25 red
                worksheet.conditional_format(f'{col_letter}2:{col_letter}{len(df_pg)}', {
                    'type': 'cell', 'criteria': '<=', 'value': 0.25, 'format': red_format
                })
                
    writer.close()
    print("Peer Comparison Excel generated!")

if __name__ == '__main__':
    df, year = compute_percentiles()
    generate_radar_charts(df)
    generate_peer_comparison_excel(df)
