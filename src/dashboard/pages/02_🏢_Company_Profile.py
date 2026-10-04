import streamlit as st
import plotly.io as pio
pio.templates.default = 'plotly_dark'
import plotly.graph_objects as go
import pandas as pd
from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_bs, get_cf, get_pros_cons

st.set_page_config(page_title="Company Profile", layout="wide")
st.title("Company Profile")

companies = get_companies()
if companies.empty:
    st.error("No companies found.")
    st.stop()

# Autocomplete dropdown
company_options = companies['company_name'] + " (" + companies['ticker'] + ")"
selected_company = st.selectbox("Search Company", company_options)

ticker = selected_company.split("(")[-1].strip(")")

company_info = companies[companies['ticker'] == ticker].iloc[0]

st.markdown(f"## {company_info['company_name']}")
st.markdown(f"**Sector:** {company_info['sector']} | **Industry:** {company_info['industry']} | **Ticker:** {company_info['ticker']}")
# About description isn't in companies table, using placeholder or checking if it exists
desc = company_info.get('description', 'Description not available in database.')
st.write(desc)

ratios = get_ratios(ticker)
if not ratios.empty:
    latest = ratios.iloc[0]
    col1, col2, col3 = st.columns(3)
    
    roe = latest.get('return_on_equity_pct', pd.NA)
    roce = latest.get('roce', pd.NA) # ROCE is not in financial_ratios unless added, I added composite score logic earlier.
    # If ROCE is missing, we can compute it if PL and BS exist
    npm = latest.get('net_profit_margin_pct', pd.NA)
    de = latest.get('debt_to_equity', pd.NA)
    rev_cagr = latest.get('revenue_cagr_5yr', pd.NA)
    fcf = latest.get('free_cash_flow_cr', pd.NA)
    
    col1.metric("ROE", f"{roe:.2f}%" if pd.notna(roe) else "N/A")
    col2.metric("ROCE", f"{roce:.2f}%" if pd.notna(roce) else "N/A")
    col3.metric("Net Profit Margin", f"{npm:.2f}%" if pd.notna(npm) else "N/A")
    
    col4, col5, col6 = st.columns(3)
    col4.metric("D/E", f"{de:.2f}" if pd.notna(de) else "N/A")
    col5.metric("Revenue CAGR 5yr", f"{rev_cagr:.2f}%" if pd.notna(rev_cagr) else "N/A")
    col6.metric("FCF (Latest)", f"{fcf:.2f}" if pd.notna(fcf) else "N/A")
    
    pl = get_pl(ticker)
    if not pl.empty:
        # 10 year bar chart for Revenue and Net Profit
        pl_10yr = pl.head(10).sort_values('year')
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=pl_10yr['year'], y=pl_10yr['sales'], name='Revenue'))
        fig.add_trace(go.Bar(x=pl_10yr['year'], y=pl_10yr['net_profit'], name='Net Profit'))
        fig.update_layout(title="Revenue & Net Profit (Last 10 Years)", barmode='group')
        st.plotly_chart(fig, use_container_width=True)
        
    # Dual axis for ROE and ROCE
    if not ratios.empty:
        r_10yr = ratios.head(10).sort_values('year')
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=r_10yr['year'], y=r_10yr['return_on_equity_pct'], name='ROE', mode='lines+markers'))
        if 'roce' in r_10yr.columns:
            fig2.add_trace(go.Scatter(x=r_10yr['year'], y=r_10yr['roce'], name='ROCE', mode='lines+markers', yaxis='y2'))
        fig2.update_layout(title="ROE & ROCE (Last 10 Years)",
                           yaxis=dict(title='ROE (%)'),
                           yaxis2=dict(title='ROCE (%)', overlaying='y', side='right'))
        st.plotly_chart(fig2, use_container_width=True)

    
    st.markdown("### Pros & Cons")
    pc = get_pros_cons(ticker)
    if not pc.empty:
        for _, row in pc.iterrows():
            typ = row.get('type', '').lower()
            text = row.get('description', '')
            if 'pro' in typ:
                st.markdown(f"✅ {text}")
            elif 'con' in typ:
                st.markdown(f"❌ {text}")
            else:
                st.markdown(f"- {text}")
else:
    st.warning("Ticker not found — please try another")
