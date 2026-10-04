import streamlit as st
import plotly.io as pio
pio.templates.default = 'plotly_dark'
import pandas as pd
import plotly.express as px
import os
from src.dashboard.utils.db import get_companies

st.set_page_config(page_title="Capital Allocation Map", layout="wide")
st.title("Capital Allocation Map")

if not os.path.exists('output/capital_allocation.csv'):
    st.error("capital_allocation.csv not found")
    st.stop()
    
alloc = pd.read_csv('output/capital_allocation.csv')
latest_year = alloc['year'].max()
alloc = alloc[alloc['year'] == latest_year]

comps = get_companies()
df = alloc.merge(comps[['company_id', 'company_name', 'ticker']], on='company_id', how='left')

st.markdown(f"### Capital Allocation Patterns ({latest_year})")

fig = px.treemap(
    df, path=[px.Constant("All Companies"), 'pattern_label', 'company_name'],
    color='pattern_label'
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Companies in Pattern")
pattern = st.selectbox("Select Pattern", df['pattern_label'].unique())
st.dataframe(df[df['pattern_label'] == pattern][['company_name', 'ticker']], use_container_width=True)
