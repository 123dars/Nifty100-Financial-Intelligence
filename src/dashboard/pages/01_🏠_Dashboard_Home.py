import streamlit as st
import plotly.io as pio
pio.templates.default = 'plotly_dark'
import plotly.express as px
import pandas as pd
from src.dashboard.utils.db import get_all_ratios, get_sectors

st.set_page_config(page_title="Home", layout="wide")
st.title("Executive Dashboard")

st.markdown('''
<style>
    /* Metric Cards Styling */
    div[data-testid="metric-container"] {
        background-color: #1E1E2E;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: scale(1.02);
        border: 1px solid #00FF7F;
    }
    /* Main Title Styling */
    h1 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 2px solid #00FF7F;
        padding-bottom: 10px;
        margin-bottom: 30px;
    }
    h3 {
        color: #A0A0A0;
        margin-top: 40px;
        font-weight: 400;
    }
</style>
''', unsafe_allow_html=True)



year = st.sidebar.selectbox("Select Year", list(range(2024, 2018, -1)))

df = get_all_ratios(year)

if not df.empty:
    avg_roe = df['return_on_equity_pct'].mean()
    med_pe = df['pe_ratio'].median()
    med_de = df['debt_to_equity'].median()
    total_companies = len(df)
    med_rev_cagr = df['revenue_cagr_5yr'].median()
    debt_free_count = len(df[df['debt_to_equity'] <= 0.1]) # Using <= 0.1 as proxy for debt-free
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Average ROE", f"{avg_roe:.2f}%" if pd.notna(avg_roe) else "N/A")
    col2.metric("Median P/E", f"{med_pe:.2f}" if pd.notna(med_pe) else "N/A")
    col3.metric("Median D/E", f"{med_de:.2f}" if pd.notna(med_de) else "N/A")
    
    col4, col5, col6 = st.columns(3)
    col4.metric("Total Companies", total_companies)
    col5.metric("Median Revenue CAGR 5yr", f"{med_rev_cagr:.2f}%" if pd.notna(med_rev_cagr) else "N/A")
    col6.metric("Debt-Free Companies", debt_free_count)
    
    st.markdown("### Sector Breakdown")
    sector_df = get_sectors()
    if not sector_df.empty:
        fig = px.pie(sector_df, values='count', names='sector', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
    st.markdown("### Top 5 Companies by Composite Score")
    if 'composite_quality_score' in df.columns:
        top_5 = df.sort_values('composite_quality_score', ascending=False).head(5)
        st.dataframe(top_5[['company_name', 'sector', 'composite_quality_score']], use_container_width=True)
else:
    st.warning("No data available for the selected year.")
