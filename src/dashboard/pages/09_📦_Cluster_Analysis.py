import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

pio.templates.default = "plotly_dark"

st.set_page_config(page_title="Cluster Analysis", layout="wide")
st.title("Cluster Analysis — 5-Cluster Stock Grouping")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
ARTIFACTS = PROJECT_ROOT / "artifacts" / "clustering"


@st.cache_data(ttl=600)
def _latest_run():
    if not DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            "SELECT run_id, created_at, n_clusters, eligible_companies, "
            "excluded_companies, inertia FROM cluster_runs "
            "ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        conn.close()
    except Exception:
        return None
    if row is None:
        return None
    return {
        "run_id": row[0],
        "created_at": row[1],
        "n_clusters": row[2],
        "eligible": row[3],
        "excluded": row[4],
        "inertia": row[5],
    }


@st.cache_data(ttl=600)
def _assignments(run_id):
    conn = sqlite3.connect(str(DB_PATH))
    try:
        df = pd.read_sql_query(
            "SELECT a.cluster_id, a.cluster_name, c.ticker, c.company_name, "
            "c.sector, a.fiscal_year FROM cluster_assignments a "
            "JOIN companies c ON c.company_id = a.company_id "
            "WHERE a.run_id = ? ORDER BY a.cluster_id, c.ticker",
            conn,
            params=[run_id],
        )
    finally:
        conn.close()
    return df


run = _latest_run()
if run is None:
    st.warning(
        "No clustering run found. Generate one with:\n\n"
        "`python scripts/run_clustering.py` (requires `uv sync --python 3.12`)."
    )
    st.stop()

st.markdown("## Section 1 — Cluster overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Eligible companies", run["eligible"])
c2.metric("Clusters configured", run["n_clusters"])
c3.metric("Excluded (no features)", run["excluded"])
c4.metric("Model inertia", f"{run['inertia']:.1f}" if run["inertia"] else "N/A")
st.caption(
    f"Run {run['run_id']} · {run['created_at']} · one row per company (latest year)"
)

df = _assignments(run["run_id"])

st.markdown("## Section 2 — Cluster distribution")
counts = df.groupby(["cluster_id", "cluster_name"]).size().reset_index(name="companies")
fig = px.bar(
    counts,
    x="cluster_name",
    y="companies",
    color="cluster_id",
    title="Companies per cluster",
)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(counts, use_container_width=True)

st.markdown("## Section 3 — Cluster profiles")
prof_path = ARTIFACTS / "cluster_profiles.csv"
if prof_path.exists():
    st.dataframe(pd.read_csv(prof_path), use_container_width=True)
else:
    st.info("cluster_profiles.csv not found — re-run scripts/run_clustering.py.")
sel = st.selectbox("Inspect cluster", sorted(df["cluster_id"].unique().tolist()))
st.dataframe(
    df[df["cluster_id"] == sel][["ticker", "company_name", "sector", "fiscal_year"]],
    use_container_width=True,
)

st.markdown("## Section 4 — Visual analysis")
for label, fname in (
    ("Elbow plot (K=1..10, K=5 selected)", "elbow.png"),
    ("Feature correlation (Pearson)", "correlation_heatmap.png"),
):
    p = ARTIFACTS / fname
    st.subheader(label)
    if p.exists():
        st.image(str(p))
    else:
        st.info(f"{fname} not found.")
    st.caption(
        "Elbow inertia falls as K rises (diagnostic only; final model uses K=5). "
        "Correlation shows association between features, not causation."
    )

st.markdown("## Section 5 — Outlier analysis (|z| > 3)")
out_path = ARTIFACTS / "outliers.csv"
if out_path.exists():
    out = pd.read_csv(out_path)
    f1 = st.multiselect("Feature", sorted(out["feature"].unique().tolist()))
    f2 = st.multiselect("Cluster", sorted(out["cluster_id"].unique().tolist()))
    view = out
    if f1:
        view = view[view["feature"].isin(f1)]
    if f2:
        view = view[view["cluster_id"].isin(f2)]
    st.metric("Outlier observations", len(view))
    st.dataframe(view, use_container_width=True)
else:
    st.info("outliers.csv not found.")

st.markdown("## Section 6 — Universe statistics (unweighted)")
st.caption(
    "nifty100.db holds no portfolio holdings/weights table, so figures "
    "below describe the company universe — not an invested portfolio."
)
shares = df.groupby("cluster_id").size().reset_index(name="companies")
shares["share_pct"] = (100 * shares["companies"] / len(df)).round(2)
st.dataframe(shares, use_container_width=True)
