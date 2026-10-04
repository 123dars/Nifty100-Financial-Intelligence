import streamlit as st
import pandas as pd
from src.dashboard.utils.db import get_all_ratios

st.set_page_config(page_title="Screener", layout="wide")
st.title("Financial Screener")

presets = {
    'Quality Compounder': {'roe_min': 15.0, 'de_max': 1.0, 'fcf_min': 0.0, 'rev_cagr_min': 10.0, 'pat_cagr_min': 0.0, 'opm_min': 0.0, 'pe_max': 200.0, 'pb_max': 50.0, 'dy_min': 0.0, 'icr_min': 0.0},
    'Value Pick': {'roe_min': 0.0, 'de_max': 2.0, 'fcf_min': -100000.0, 'rev_cagr_min': 0.0, 'pat_cagr_min': 0.0, 'opm_min': 0.0, 'pe_max': 20.0, 'pb_max': 3.0, 'dy_min': 1.0, 'icr_min': 0.0},
    'Growth Accelerator': {'roe_min': 0.0, 'de_max': 2.0, 'fcf_min': -100000.0, 'rev_cagr_min': 15.0, 'pat_cagr_min': 20.0, 'opm_min': 0.0, 'pe_max': 200.0, 'pb_max': 50.0, 'dy_min': 0.0, 'icr_min': 0.0},
    'Dividend Champion': {'roe_min': 0.0, 'de_max': 100.0, 'fcf_min': 0.0, 'rev_cagr_min': 0.0, 'pat_cagr_min': 0.0, 'opm_min': 0.0, 'pe_max': 200.0, 'pb_max': 50.0, 'dy_min': 2.0, 'icr_min': 0.0},
    'Debt-Free Blue Chip': {'roe_min': 12.0, 'de_max': 0.1, 'fcf_min': -100000.0, 'rev_cagr_min': 0.0, 'pat_cagr_min': 0.0, 'opm_min': 0.0, 'pe_max': 200.0, 'pb_max': 50.0, 'dy_min': 0.0, 'icr_min': 0.0},
    'Turnaround Watch': {'roe_min': 0.0, 'de_max': 100.0, 'fcf_min': 0.0, 'rev_cagr_min': 10.0, 'pat_cagr_min': 0.0, 'opm_min': 0.0, 'pe_max': 200.0, 'pb_max': 50.0, 'dy_min': 0.0, 'icr_min': 0.0}
}

for k in presets['Quality Compounder'].keys():
    if k not in st.session_state:
        # Defaults
        val = 0.0
        if 'max' in k:
            val = 200.0 if k == 'pe_max' else 100.0
            if k == 'fcf_min': val = -100000.0
        st.session_state[k] = val
if 'fcf_min' not in st.session_state:
    st.session_state['fcf_min'] = -100000.0

st.sidebar.markdown("### Presets")
cols = st.sidebar.columns(2)
for i, (name, vals) in enumerate(presets.items()):
    if cols[i%2].button(name):
        for k, v in vals.items():
            st.session_state[k] = v

st.sidebar.markdown("### Filters")
roe_min = st.sidebar.slider("ROE Min (%)", -50.0, 100.0, float(st.session_state.roe_min), key="roe_min")
de_max = st.sidebar.slider("D/E Max", 0.0, 50.0, float(st.session_state.de_max), key="de_max")
fcf_min = st.sidebar.slider("FCF Min (Cr)", -100000.0, 100000.0, float(st.session_state.fcf_min), key="fcf_min")
rev_cagr_min = st.sidebar.slider("Rev CAGR Min (%)", -50.0, 100.0, float(st.session_state.rev_cagr_min), key="rev_cagr_min")
pat_cagr_min = st.sidebar.slider("PAT CAGR Min (%)", -50.0, 100.0, float(st.session_state.pat_cagr_min), key="pat_cagr_min")
opm_min = st.sidebar.slider("OPM Min (%)", -50.0, 100.0, float(st.session_state.opm_min), key="opm_min")
pe_max = st.sidebar.slider("P/E Max", 0.0, 500.0, float(st.session_state.pe_max), key="pe_max")
pb_max = st.sidebar.slider("P/B Max", 0.0, 100.0, float(st.session_state.pb_max), key="pb_max")
dy_min = st.sidebar.slider("Div Yield Min (%)", 0.0, 20.0, float(st.session_state.dy_min), key="dy_min")
icr_min = st.sidebar.slider("ICR Min", -10.0, 100.0, float(st.session_state.icr_min), key="icr_min")

df = get_all_ratios(2024)
if df.empty:
    st.warning("No data for 2024")
    st.stop()

# Convert to numeric
numeric_cols = ['return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr', 'revenue_cagr_5yr', 'pat_cagr_5yr', 
                'operating_profit_margin_pct', 'pe_ratio', 'pb_ratio', 'dividend_yield', 'interest_coverage']
for c in numeric_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')

# Apply filters
filtered = df[
    (df['return_on_equity_pct'].fillna(-999) >= roe_min) &
    (df['debt_to_equity'].fillna(999) <= de_max) &
    (df['free_cash_flow_cr'].fillna(-999999) >= fcf_min) &
    (df['revenue_cagr_5yr'].fillna(-999) >= rev_cagr_min) &
    (df['pat_cagr_5yr'].fillna(-999) >= pat_cagr_min) &
    (df['operating_profit_margin_pct'].fillna(-999) >= opm_min) &
    (df['pe_ratio'].fillna(9999) <= pe_max) &
    (df['pb_ratio'].fillna(9999) <= pb_max) &
    (df['dividend_yield'].fillna(-999) >= dy_min) &
    (df['interest_coverage'].fillna(-999) >= icr_min)
]

st.markdown(f"**{len(filtered)} companies match your filters**")

display_cols = ['company_id', 'company_name', 'sector', 'composite_quality_score'] + numeric_cols
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(filtered[display_cols], use_container_width=True)

csv = filtered[display_cols].to_csv(index=False).encode('utf-8')
st.download_button(
    "Download CSV",
    csv,
    "screener_results.csv",
    "text/csv"
)
