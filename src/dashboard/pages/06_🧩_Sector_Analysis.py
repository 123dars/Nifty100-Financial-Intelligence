import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import streamlit as st
import plotly.io as pio
pio.templates.default = 'plotly_dark'
import pandas as pd
import plotly.express as px
from src.dashboard.utils.db import get_all_ratios, get_companies
import os

st.set_page_config(page_title="Sector Analysis", layout="wide")
st.title("Sector Analysis")

comps = get_companies()
sectors = comps['sector'].dropna().unique()
selected_sector = st.selectbox("Select Sector", sectors)

df = get_all_ratios(2024)
df = df.merge(comps[['company_id', 'industry']], on='company_id', how='left')

# Load market cap
mc = pd.DataFrame()
if os.path.exists('data/market_cap.xlsx'):
    mc = pd.read_excel('data/market_cap.xlsx')
    
if not mc.empty:
    df = df.merge(mc[['company_id', 'market_cap_crore']], on='company_id', how='left')
else:
    df['market_cap_crore'] = 1000

df_sector = df[df['sector'] == selected_sector].copy()

if df_sector.empty:
    st.warning("No data for this sector")
    st.stop()

# Convert
for c in ['revenue_cagr_5yr', 'return_on_equity_pct', 'market_cap_crore', 'net_profit_margin_pct', 'debt_to_equity']:
    if c in df_sector.columns:
        df_sector[c] = pd.to_numeric(df_sector[c], errors='coerce')

# Drop NA for bubble chart
df_bubble = df_sector.dropna(subset=['revenue_cagr_5yr', 'return_on_equity_pct'])
df_bubble['market_cap_crore'] = df_bubble['market_cap_crore'].fillna(1000).clip(lower=100)

st.markdown("### Revenue CAGR vs ROE Bubble Chart")
fig = px.scatter(
    df_bubble, x='revenue_cagr_5yr', y='return_on_equity_pct',
    size='market_cap_crore', color='industry', hover_name='company_name',
    labels={'revenue_cagr_5yr': 'Revenue CAGR 5yr (%)', 'return_on_equity_pct': 'ROE (%)'}
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Sector Median KPIs")
medians = df_sector[['return_on_equity_pct', 'net_profit_margin_pct', 'debt_to_equity', 'revenue_cagr_5yr']].median().reset_index()
medians.columns = ['Metric', 'Median Value']
fig2 = px.bar(medians, x='Metric', y='Median Value', text='Median Value')
fig2.update_traces(texttemplate='%{text:.2f}', textposition='outside')
st.plotly_chart(fig2, use_container_width=True)
