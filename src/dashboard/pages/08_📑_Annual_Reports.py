import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import streamlit as st
import pandas as pd
import sqlite3
import requests
from src.dashboard.utils.db import get_companies

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports")

comps = get_companies()
selected_company = st.selectbox("Search Company", comps['company_name'] + " (" + comps['ticker'] + ")")
ticker = selected_company.split("(")[-1].strip(")")
cid = comps[comps['ticker'] == ticker]['company_id'].iloc[0]

conn = sqlite3.connect('nifty100.db')
docs = pd.read_sql_query("SELECT * FROM documents WHERE company_id = ? AND document_type = 'annual_report' ORDER BY document_date DESC", conn, params=[int(cid)])
conn.close()

if docs.empty:
    st.warning("No annual reports found.")
else:
    for _, row in docs.iterrows():
        year = str(row['document_date'])[:4]
        url = row['document_url']
        col1, col2 = st.columns([3, 1])
        col1.markdown(f"**{year} Annual Report**")
        
        # Check URL
        try:
            r = requests.head(url, timeout=2)
            if r.status_code == 404:
                col2.markdown(" :red[Report unavailable]")
            else:
                col2.markdown(f"[Download PDF]({url})")
        except:
            # If timeout or error, just show the link
            col2.markdown(f"[Download PDF]({url})")
