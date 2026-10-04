import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path

DB_PATH = Path("nifty100.db")

@st.cache_data(ttl=600)
def _query(sql, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_companies():
    return _query("SELECT * FROM companies")

@st.cache_data(ttl=600)
def get_all_ratios(year):
    sql = """
    SELECT f.*, c.company_name, c.sector, s.pe_ratio, s.pb_ratio, s.dividend_yield
    FROM financial_ratios f
    JOIN companies c ON f.company_id = c.company_id
    LEFT JOIN financial_ratios_source s ON f.company_id = s.company_id AND f.year = s.year
    WHERE f.year = ?
    """
    return _query(sql, [year])

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    sql = """
    SELECT f.* FROM financial_ratios f
    JOIN companies c ON f.company_id = c.company_id
    WHERE c.ticker = ?
    """
    params = [ticker]
    if year:
        sql += " AND f.year = ?"
        params.append(year)
    sql += " ORDER BY f.year DESC"
    return _query(sql, params)

@st.cache_data(ttl=600)
def get_pl(ticker):
    sql = """
    SELECT p.* FROM profitandloss p
    JOIN companies c ON p.company_id = c.company_id
    WHERE c.ticker = ?
    ORDER BY p.year DESC
    """
    return _query(sql, [ticker])

@st.cache_data(ttl=600)
def get_bs(ticker):
    sql = """
    SELECT b.* FROM balancesheet b
    JOIN companies c ON b.company_id = c.company_id
    WHERE c.ticker = ?
    ORDER BY b.year DESC
    """
    return _query(sql, [ticker])

@st.cache_data(ttl=600)
def get_cf(ticker):
    sql = """
    SELECT cf.* FROM cashflow cf
    JOIN companies c ON cf.company_id = c.company_id
    WHERE c.ticker = ?
    ORDER BY cf.year DESC
    """
    return _query(sql, [ticker])

@st.cache_data(ttl=600)
def get_sectors():
    return _query("SELECT sector, COUNT(company_id) as count FROM companies GROUP BY sector")

@st.cache_data(ttl=600)
def get_peers(group_name):
    sql = """
    SELECT p.*, c.company_name, c.ticker
    FROM peer_percentiles p
    JOIN companies c ON p.company_id = c.company_id
    WHERE p.peer_group_name = ?
    """
    return _query(sql, [group_name])

@st.cache_data(ttl=600)
def get_valuation(ticker):
    import os
    if os.path.exists('output/valuation_summary.xlsx'):
        df = pd.read_excel('output/valuation_summary.xlsx')
        comps = get_companies()
        cid = comps[comps['ticker'] == ticker]['company_id'].iloc[0]
        return df[df['company_id'] == cid]
    return pd.DataFrame()

@st.cache_data(ttl=600)
def get_pros_cons(ticker):
    sql = """
    SELECT pc.* FROM prosandcons pc
    JOIN companies c ON pc.company_id = c.company_id
    WHERE c.ticker = ?
    """
    return _query(sql, [ticker])
