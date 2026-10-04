import streamlit as st
import plotly.io as pio
pio.templates.default = 'plotly_dark'
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sqlite3
from pathlib import Path

st.set_page_config(page_title="Peer Comparison", layout="wide")
st.title("Peer Comparison")

DB_PATH = Path("nifty100.db")

@st.cache_data(ttl=600)
def get_unique_peer_groups():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT DISTINCT peer_group_name FROM peer_percentiles WHERE peer_group_name IS NOT NULL", conn)
        conn.close()
        return df['peer_group_name'].tolist()
    except:
        return []

@st.cache_data(ttl=600)
def get_peer_data(group_name):
    conn = sqlite3.connect(DB_PATH)
    sql = """
    SELECT p.*, c.company_name, c.ticker, f.composite_quality_score, f.return_on_equity_pct as roe,
           f.net_profit_margin_pct as npm, f.debt_to_equity as de, f.free_cash_flow_cr as fcf,
           f.pat_cagr_5yr as pat_cagr, f.revenue_cagr_5yr as rev_cagr,
           pl.operating_profit, pl.other_income, bs.equity, bs.reserves, bs.borrowings
    FROM peer_percentiles p
    JOIN companies c ON p.company_id = c.company_id
    JOIN financial_ratios f ON p.company_id = f.company_id AND p.year = f.year
    LEFT JOIN profitandloss pl ON p.company_id = pl.company_id AND p.year = pl.year
    LEFT JOIN balancesheet bs ON p.company_id = bs.company_id AND p.year = bs.year
    WHERE p.peer_group_name = ?
    """
    df = pd.read_sql_query(sql, conn, params=[group_name])
    conn.close()
    
    # Calculate ROCE
    for c in ['operating_profit', 'other_income', 'equity', 'reserves', 'borrowings']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    ebit = df['operating_profit'].fillna(0) + df['other_income'].fillna(0)
    ce = df['equity'].fillna(0) + df['reserves'].fillna(0) + df['borrowings'].fillna(0)
    df['roce'] = np.where(ce > 0, ebit / ce * 100, np.nan)
    return df

groups = get_unique_peer_groups()
if not groups:
    st.warning("No peer groups found.")
    st.stop()

selected_group = st.selectbox("Select Peer Group", groups)

df = get_peer_data(selected_group)
# df contains multiple rows per company because of peer_percentiles (1 row per metric).
# Let's pivot the percentiles if needed, but we also have the raw metrics joined.
# It's better to just get unique companies from df.
companies = df[['company_id', 'company_name', 'ticker']].drop_duplicates()

selected_company = st.selectbox("Select Company for Radar Chart", companies['company_name'] + " (" + companies['ticker'] + ")")
ticker = selected_company.split("(")[-1].strip(")")
company_id = companies[companies['ticker'] == ticker]['company_id'].iloc[0]

# Prepare Radar Data
radar_cols = ['roe', 'roce', 'npm', 'de', 'fcf', 'pat_cagr', 'rev_cagr', 'composite_quality_score']
# Get unique company-level row for raw metrics
df_unique = df[['company_id', 'company_name'] + radar_cols].drop_duplicates()

for c in radar_cols:
    df_unique[c] = pd.to_numeric(df_unique[c], errors='coerce')

# Scale 0-1
df_scaled = df_unique.copy()
for col in radar_cols:
    vals = df_scaled[col]
    vmin, vmax = vals.min(), vals.max()
    if vmax > vmin:
        if col == 'de':
            df_scaled[col] = 1 - (vals - vmin) / (vmax - vmin)
        else:
            df_scaled[col] = (vals - vmin) / (vmax - vmin)
    else:
        df_scaled[col] = 0.5
    df_scaled[col] = df_scaled[col].fillna(0)

company_row = df_scaled[df_scaled['company_id'] == company_id].iloc[0]
avg_row = df_scaled.mean(numeric_only=True)

labels = ['ROE', 'ROCE', 'NPM', 'D/E (Inv)', 'FCF', 'PAT CAGR', 'Rev CAGR', 'Composite']
comp_vals = company_row[radar_cols].tolist()
avg_vals = avg_row[radar_cols].tolist()

# Close the radar
comp_vals += comp_vals[:1]
avg_vals += avg_vals[:1]
labels_closed = labels + [labels[0]]

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=comp_vals,
    theta=labels_closed,
    fill='toself',
    name=selected_company
))
fig.add_trace(go.Scatterpolar(
    r=avg_vals,
    theta=labels_closed,
    fill=None,
    mode='lines',
    line=dict(dash='dash', color='grey'),
    name=f"{selected_group} Average"
))
fig.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=True, title="8-Axis Radar Chart")
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Peer Group KPI Table")
# Highlight benchmark (highest composite score)
benchmark_id = df_unique.loc[df_unique['composite_quality_score'].idxmax(), 'company_id']

def highlight_benchmark(row):
    if row['company_id'] == benchmark_id:
        return ['background-color: gold'] * len(row)
    return [''] * len(row)

styled_df = df_unique.style.apply(highlight_benchmark, axis=1)
st.dataframe(styled_df, use_container_width=True)
