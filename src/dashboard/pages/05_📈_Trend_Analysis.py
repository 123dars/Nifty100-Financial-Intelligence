import streamlit as st
import plotly.io as pio
pio.templates.default = 'plotly_dark'
import pandas as pd
import plotly.graph_objects as go
from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Trend Analysis")

companies = get_companies()
selected_company = st.selectbox("Search Company", companies['company_name'] + " (" + companies['ticker'] + ")")
ticker = selected_company.split("(")[-1].strip(")")

ratios = get_ratios(ticker).head(10).sort_values('year')

if ratios.empty:
    st.warning("No data available")
    st.stop()

# Convert to numeric
numeric_cols = [c for c in ratios.columns if c not in ('company_id', 'year', 'ticker', 'company_name', 'sector', 'industry')]
for c in numeric_cols:
    ratios[c] = pd.to_numeric(ratios[c], errors='coerce')

metrics = st.multiselect("Select up to 3 metrics", numeric_cols, default=['return_on_equity_pct'])
if len(metrics) > 3:
    st.warning("Please select at most 3 metrics")
    metrics = metrics[:3]

if metrics:
    fig = go.Figure()
    for m in metrics:
        vals = ratios[m]
        # Calculate YoY % change
        yoy = vals.pct_change() * 100
        text = [f"{v:.1f}% YoY" if pd.notna(v) else "" for v in yoy]
        
        fig.add_trace(go.Scatter(
            x=ratios['year'], y=vals, mode='lines+markers+text',
            name=m, text=text, textposition="top center"
        ))
    fig.update_layout(title=f"Trend Analysis for {ticker}", height=600)
    st.plotly_chart(fig, use_container_width=True)
