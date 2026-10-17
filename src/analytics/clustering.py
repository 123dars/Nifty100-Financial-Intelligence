"""Sprint 6 — Stock clustering & profiling over Sprint 2 financial ratios.

Pipeline:
    financial_ratios (+ vendor PE/yield) — one row per company at latest year
      -> median imputation -> StandardScaler -> elbow (K=1..10, diagnostic)
      -> KMeans (exactly K=5) -> cluster_assignments / cluster_runs tables
      -> profiles (observed units), names, correlation heatmap,
         |z|>3 outliers, unweighted universe stats.

Read-only w.r.t. source financial tables; writes only clustering result
tables + artifact files. sklearn / matplotlib are imported lazily inside
the functions that need them so data-loading, validation, profiling and
outlier math stay usable without the heavy deps installed.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "clustering_config.yaml"
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"

SOURCE_TABLES = ("financial_ratios", "financial_ratios_source")
# Columns that must never enter KMeans even if configured by mistake.
FORBIDDEN_COLUMNS = {
    "company_id",
    "ticker",
    "company_name",
    "sector",
    "industry",
    "year",
    "ratio_id",
    "cluster_id",
    "cluster_name",
    "run_id",
}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def load_clustering_config(path: str | Path | None = None) -> dict:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Clustering config not found: {cfg_path}")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Malformed clustering YAML at {cfg_path}: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError(
            f"Malformed clustering YAML at {cfg_path}: top level must be a mapping"
        )
    return validate_clustering_config(config)


def validate_clustering_config(config: dict) -> dict:
    if "version" not in config:
        raise ValueError("Invalid clustering config: missing 'version'")
    clustering = config.get("clustering")
    if not isinstance(clustering, dict):
        raise ValueError("Invalid clustering config: missing 'clustering' mapping")
    features = clustering.get("feature_columns")
    if not isinstance(features, list) or not features:
        raise ValueError(
            "Invalid clustering config: 'clustering.feature_columns' must be a "
            "non-empty list of validated financial columns"
        )
    forbidden = [c for c in features if c in FORBIDDEN_COLUMNS]
    if forbidden:
        raise ValueError(
            f"Invalid clustering config: identifier columns must not be clustered: {forbidden}"
        )
    if len(set(features)) != len(features):
        raise ValueError(
            "Invalid clustering config: 'feature_columns' contains duplicates"
        )
    n_clusters = clustering.get("n_clusters", 5)
    if n_clusters != 5:
        raise ValueError(
            f"Invalid clustering config: assignment requires n_clusters=5, got {n_clusters}"
        )
    return config


def clustering_settings(config: dict) -> dict:
    return config["clustering"]


# ---------------------------------------------------------------------------
# Schema helpers (injection-safe column validation)
# ---------------------------------------------------------------------------


def table_columns(db_path: str | Path, table: str) -> set[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    finally:
        conn.close()
    return {r[1] for r in rows}


def validate_feature_columns(
    db_path: str | Path, feature_columns: list[str], feature_sources: dict | None = None
) -> dict[str, str]:
    """Map each feature -> owning table. Raises ValueError listing unknown columns."""
    ratios_cols = table_columns(db_path, "financial_ratios")
    source_cols = table_columns(db_path, "financial_ratios_source")
    mapping: dict[str, str] = {}
    unknown: list[str] = []
    for feat in feature_columns:
        if feature_sources and feat in feature_sources:
            table = feature_sources[feat]
            cols = ratios_cols if table == "financial_ratios" else source_cols
            if feat not in cols:
                unknown.append(feat)
            else:
                mapping[feat] = table
        elif feat in ratios_cols:
            mapping[feat] = "financial_ratios"
        elif feat in source_cols:
            mapping[feat] = "financial_ratios_source"
        else:
            unknown.append(feat)
    if unknown:
        known = sorted(ratios_cols | source_cols)
        raise ValueError(
            f"Unknown clustering feature(s) {unknown}. "
            f"Expected columns from financial_ratios / financial_ratios_source, e.g.: "
            f"{known[:12]}..."
        )
    return mapping


# ---------------------------------------------------------------------------
# Data loading — one row per company
# ---------------------------------------------------------------------------


def load_company_features(
    db_path: str | Path | None = None,
    feature_columns: list[str] | None = None,
    as_of_year: int | None = None,
    config: dict | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Load one feature row per company at the latest (or given) fiscal year.

    Returns (frame, summary). Frame holds company_id/ticker/company_name/
    sector/year plus numeric feature columns (inf coerced to NaN).
    """
    db = str(db_path) if db_path else str(DEFAULT_DB_PATH)
    if config is None:
        config = load_clustering_config()
    settings = clustering_settings(config)
    features = (
        list(feature_columns) if feature_columns else list(settings["feature_columns"])
    )
    sources = settings.get("feature_sources") or {}
    if as_of_year is None:
        as_of_year = settings.get("as_of_year")
    mapping = validate_feature_columns(db, features, sources)

    ratio_feats = [f for f in features if mapping[f] == "financial_ratios"]
    source_feats = [f for f in features if mapping[f] == "financial_ratios_source"]

    f_select = ", ".join(f'f."{c}" AS "{c}"' for c in ratio_feats)
    s_select = ", ".join(f's."{c}" AS "{c}"' for c in source_feats)
    selects = ", ".join(s for s in (f_select, s_select) if s)

    conn = sqlite3.connect(db)
    try:
        if as_of_year is not None:
            sql = f"""
            SELECT c.company_id, c.ticker, c.company_name, c.sector,
                   f.year AS year, {selects}
            FROM companies c
            JOIN financial_ratios f ON f.company_id = c.company_id AND f.year = ?
            LEFT JOIN financial_ratios_source s
                   ON s.company_id = c.company_id AND s.year = f.year
            ORDER BY c.ticker
            """
            df = pd.read_sql_query(sql, conn, params=[as_of_year])
            period = as_of_year
        else:
            sql = f"""
            SELECT c.company_id, c.ticker, c.company_name, c.sector,
                   f.year AS year, {selects}
            FROM companies c
            JOIN financial_ratios f ON f.company_id = c.company_id
            LEFT JOIN financial_ratios_source s
                   ON s.company_id = c.company_id AND s.year = f.year
            JOIN (SELECT company_id, MAX(year) AS max_year
                  FROM financial_ratios GROUP BY company_id) m
              ON m.company_id = c.company_id AND m.max_year = f.year
            ORDER BY c.ticker
            """
            df = pd.read_sql_query(sql, conn, params=[])
            period = "latest_available_year"
    finally:
        conn.close()

    if df["company_id"].duplicated().any():
        dupes = df.loc[df["company_id"].duplicated(), "company_id"].tolist()
        raise ValueError(f"Duplicate company grain in clustering input: {dupes}")

    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[features] = df[features].replace([np.inf, -np.inf], np.nan)

    usable = df[features].notna().any(axis=1)
    excluded = df.loc[~usable].copy()
    kept = df.loc[usable].copy()
    summary = {
        "period": period,
        "records_loaded": len(df),
        "retained": len(kept),
        "excluded_no_usable_features": len(excluded),
        "excluded_company_ids": excluded["company_id"].tolist(),
        "missing_before": {c: int(kept[c].isna().sum()) for c in features},
    }
    return kept.reset_index(drop=True), summary


# ---------------------------------------------------------------------------
# Preprocessing: median imputation -> StandardScaler
# ---------------------------------------------------------------------------


def preprocess_features(
    df: pd.DataFrame,
    feature_columns: list[str],
    imputation_strategy: str = "median",
) -> dict:
    """Impute then scale. Returns scaled matrix + fitted artifacts + audit info."""
    if imputation_strategy != "median":
        raise ValueError(
            f"Unsupported imputation_strategy '{imputation_strategy}'. Expected 'median'"
        )
    if df.empty:
        raise ValueError("Cannot preprocess clustering features: no eligible companies")
    missing_before = {c: int(df[c].isna().sum()) for c in feature_columns}
    all_empty = [c for c in feature_columns if df[c].notna().sum() == 0]
    retained = [c for c in feature_columns if c not in all_empty]
    if not retained:
        raise ValueError("Cannot cluster: every configured feature is entirely missing")
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler

    constant = [c for c in retained if df[c].dropna().nunique() <= 1]

    imputer = SimpleImputer(strategy="median")
    imputed = imputer.fit_transform(df[retained].to_numpy(dtype=float))
    if np.isnan(imputed).any():
        raise ValueError(
            "Median imputation left NaNs: a retained feature has no observed values"
        )
    scaler = StandardScaler()
    scaled = scaler.fit_transform(imputed)
    return {
        "scaled": scaled,
        "retained_features": retained,
        "removed_features": all_empty,
        "constant_features": constant,
        "missing_before": missing_before,
        "missing_after": {c: 0 for c in retained},
        "imputer": imputer,
        "scaler": scaler,
    }


# ---------------------------------------------------------------------------
# Elbow + KMeans (exactly 5 clusters)
# ---------------------------------------------------------------------------


def elbow_analysis(
    scaled: np.ndarray,
    max_k: int = 10,
    random_state: int = 42,
    n_init: int = 10,
    highlight_k: int = 5,
    save_path: str | Path | None = None,
) -> dict:
    from sklearn.cluster import KMeans

    n = int(scaled.shape[0])
    max_k = max(1, min(int(max_k), n, 10))
    ks = list(range(1, max_k + 1))
    inertias: list[float] = []
    for k in ks:
        model = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        model.fit(scaled)
        inertias.append(float(model.inertia_))
    result = {"k_values": ks, "inertias": inertias}
    if save_path is not None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(ks, inertias, marker="o")
        if highlight_k in ks:
            idx = ks.index(highlight_k)
            ax.scatter([highlight_k], [inertias[idx]], s=90, zorder=5)
            ax.annotate(
                f"K={highlight_k} (selected)",
                (highlight_k, inertias[idx]),
                textcoords="offset points",
                xytext=(8, 8),
            )
        ax.set_xlabel("Number of clusters (K)")
        ax.set_ylabel("Inertia (within-cluster sum of squares)")
        ax.set_title(
            "Elbow analysis — inertia decreases as K increases; final model uses K=5"
        )
        ax.set_xticks(ks)
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        result["plot_path"] = str(path)
    return result


def fit_kmeans(
    scaled: np.ndarray,
    n_clusters: int = 5,
    random_state: int = 42,
    n_init: int = 10,
    max_iter: int = 300,
) -> Any:
    if n_clusters != 5:
        raise ValueError(f"Assignment requires n_clusters=5, got {n_clusters}")
    if np.asarray(scaled).shape[0] < n_clusters:
        raise ValueError(
            f"Not enough eligible companies for 5 clusters: got {np.asarray(scaled).shape[0]}"
        )
    from sklearn.cluster import KMeans

    model = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=n_init,
        max_iter=max_iter,
    )
    model.fit(scaled)
    return model


# ---------------------------------------------------------------------------
# Storage — dedicated result tables, transactional, never touches ratios
# ---------------------------------------------------------------------------

ASSIGNMENTS_DDL = """
CREATE TABLE IF NOT EXISTS cluster_assignments (
    run_id TEXT NOT NULL,
    company_id INTEGER NOT NULL,
    fiscal_year INTEGER NOT NULL,
    cluster_id INTEGER NOT NULL,
    cluster_name TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, company_id)
);
"""

RUNS_DDL = """
CREATE TABLE IF NOT EXISTS cluster_runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    n_clusters INTEGER NOT NULL,
    feature_names TEXT NOT NULL,
    random_state INTEGER NOT NULL,
    eligible_companies INTEGER NOT NULL,
    excluded_companies INTEGER NOT NULL,
    inertia REAL,
    preprocessing TEXT NOT NULL
);
"""


def save_results(
    db_path: str | Path | None,
    run_id: str,
    frame: pd.DataFrame,
    labels: np.ndarray,
    cluster_names: dict[int, str],
    summary: dict,
    retained_features: list[str],
    random_state: int,
    inertia: float | None,
    imputation_strategy: str = "median",
) -> dict:
    db = str(db_path) if db_path else str(DEFAULT_DB_PATH)
    created_at = datetime.now(UTC).isoformat()
    rows = [
        (run_id, int(cid), int(yr), int(lbl), cluster_names.get(int(lbl)), created_at)
        for cid, yr, lbl in zip(frame["company_id"], frame["year"], labels)
    ]
    if len({r[1] for r in rows}) != len(rows):
        raise ValueError("Duplicate company assignment within run")
    meta = {
        "run_id": run_id,
        "created_at": created_at,
        "n_clusters": 5,
        "feature_names": retained_features,
        "random_state": random_state,
        "eligible_companies": len(frame),
        "excluded_companies": int(summary.get("excluded_no_usable_features", 0)),
        "inertia": None if inertia is None else float(inertia),
        "preprocessing": {
            "imputation": imputation_strategy,
            "scaler": "StandardScaler",
        },
    }
    conn = sqlite3.connect(db)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(ASSIGNMENTS_DDL + RUNS_DDL)
        with conn:  # transaction: all-or-nothing per run
            conn.execute("DELETE FROM cluster_assignments WHERE run_id = ?", (run_id,))
            conn.execute("DELETE FROM cluster_runs WHERE run_id = ?", (run_id,))
            conn.executemany(
                "INSERT INTO cluster_assignments "
                "(run_id, company_id, fiscal_year, cluster_id, cluster_name, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.execute(
                "INSERT INTO cluster_runs (run_id, created_at, n_clusters, feature_names, "
                "random_state, eligible_companies, excluded_companies, inertia, preprocessing) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    created_at,
                    5,
                    json.dumps(retained_features),
                    random_state,
                    meta["eligible_companies"],
                    meta["excluded_companies"],
                    meta["inertia"],
                    json.dumps(meta["preprocessing"]),
                ),
            )
    finally:
        conn.close()
    meta["assignments_written"] = len(rows)
    return meta


def load_assignments(
    db_path: str | Path | None = None, run_id: str | None = None
) -> pd.DataFrame:
    db = str(db_path) if db_path else str(DEFAULT_DB_PATH)
    conn = sqlite3.connect(db)
    try:
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "cluster_assignments" not in tables:
            return pd.DataFrame()
        if run_id is None:
            row = conn.execute(
                "SELECT run_id FROM cluster_runs ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if row is None:
                return pd.DataFrame()
            run_id = row[0]
        return pd.read_sql_query(
            "SELECT a.*, c.ticker, c.company_name, c.sector "
            "FROM cluster_assignments a JOIN companies c "
            "ON c.company_id = a.company_id WHERE a.run_id = ? ORDER BY c.ticker",
            conn,
            params=[run_id],
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Day 37 — profiles, names, heatmap, outliers, universe stats
# ---------------------------------------------------------------------------


def cluster_profiles(
    frame: pd.DataFrame, labels: np.ndarray, features: list[str]
) -> pd.DataFrame:
    """Means/medians from OBSERVED values (never scaled/imputed-as-real)."""
    work = frame[["company_id", "ticker"] + features].copy()
    work["cluster_id"] = np.asarray(labels, dtype=int)
    total = len(work)
    records = []
    for cid in sorted(work["cluster_id"].unique()):
        sub = work[work["cluster_id"] == cid]
        rec: dict[str, Any] = {
            "cluster_id": int(cid),
            "company_count": len(sub),
            "share_pct": round(100.0 * len(sub) / total, 2) if total else 0.0,
        }
        for feat in features:
            observed = sub[feat].dropna()
            rec[f"{feat}_mean"] = float(observed.mean()) if len(observed) else None
            rec[f"{feat}_median"] = float(observed.median()) if len(observed) else None
            rec[f"{feat}_missing"] = int(sub[feat].isna().sum())
        records.append(rec)
    return pd.DataFrame(records).sort_values("cluster_id").reset_index(drop=True)


def assign_cluster_names(profiles: pd.DataFrame, features: list[str]) -> dict[int, str]:
    """Deterministic rule-based names from medians vs overall medians.

    Compares each cluster median to the median-of-medians reference per
    metric group (profitability / growth / leverage / valuation). Falls back
    to a neutral label so every cluster is named exactly once.
    """
    groups = {
        "profitability": [
            f
            for f in (
                "return_on_equity_pct",
                "net_profit_margin_pct",
                "operating_profit_margin_pct",
            )
            if f in features
        ],
        "growth": [f for f in ("revenue_cagr_5yr", "pat_cagr_5yr") if f in features],
        "leverage": [f for f in ("debt_to_equity",) if f in features],
        "valuation": [f for f in ("pe_ratio", "dividend_yield") if f in features],
    }
    ref: dict[str, float] = {}
    for feat in features:
        med_col = f"{feat}_median"
        if med_col in profiles.columns:
            vals = profiles[med_col].dropna()
            if len(vals):
                ref[feat] = float(vals.median())

    names: dict[int, str] = {}
    used: set[str] = set()
    for _, row in profiles.iterrows():
        cid = int(row["cluster_id"])
        traits: list[str] = []

        def med(feat: str) -> float | None:
            v = row.get(f"{feat}_median")
            return (
                None
                if v is None or (isinstance(v, float) and np.isnan(v))
                else float(v)
            )

        roe, npm = med("return_on_equity_pct"), med("net_profit_margin_pct")
        if roe is not None and "return_on_equity_pct" in ref:
            if roe >= ref["return_on_equity_pct"] * 1.25:
                traits.append("High Profitability")
            elif roe <= ref["return_on_equity_pct"] * 0.6:
                traits.append("Low Profitability")
        if not traits and npm is not None and "net_profit_margin_pct" in ref:
            if npm >= ref["net_profit_margin_pct"] * 1.25:
                traits.append("High Profitability")

        rev = med("revenue_cagr_5yr")
        if rev is not None and "revenue_cagr_5yr" in ref:
            if rev >= ref["revenue_cagr_5yr"] * 1.3:
                traits.append("Growth-Oriented")
            elif rev <= max(ref["revenue_cagr_5yr"] * 0.5, 0):
                traits.append("Slow Growth")

        de = med("debt_to_equity")
        if de is not None:
            if de <= 0.3:
                traits.append("Low-Leverage")
            elif de >= 1.5:
                traits.append("High-Leverage")

        dy = med("dividend_yield")
        if (
            dy is not None
            and "dividend_yield" in ref
            and dy >= ref["dividend_yield"] * 1.4
        ):
            traits.append("Dividend-Tilted")

        label = (
            " + ".join(traits[:2]) + " Companies"
            if traits
            else f"Balanced Financial Profile — Cluster {cid}"
        )
        if label in used:  # guarantee uniqueness, keep numeric ID visible
            label = f"{label} (Cluster {cid})"
        used.add(label)
        names[cid] = label
    return names


def correlation_heatmap(
    frame: pd.DataFrame,
    features: list[str],
    save_path: str | Path | None = None,
    method: str = "pearson",
) -> pd.DataFrame:
    """Pearson correlation on observed values. IDs/years/clusters excluded."""
    corr = frame[features].corr(method=method, numeric_only=True)
    if save_path is not None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(corr.to_numpy(dtype=float), vmin=-1, vmax=1)
        ax.set_xticks(range(len(features)), features, rotation=45, ha="right")
        ax.set_yticks(range(len(features)), features)
        for i in range(len(features)):
            for j in range(len(features)):
                v = corr.iloc[i, j]
                ax.text(
                    j,
                    i,
                    f"{v:.2f}" if pd.notna(v) else "n/a",
                    ha="center",
                    va="center",
                    fontsize=7,
                )
        ax.set_title(f"Feature correlation ({method}) — association, not causation")
        fig.colorbar(im, ax=ax, label="correlation (-1 to +1)")
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
    return corr


def detect_outliers(
    frame: pd.DataFrame,
    labels: np.ndarray,
    features: list[str],
    z_threshold: float = 3.0,
) -> pd.DataFrame:
    """Flag |z|>3 on OBSERVED values. Constant/NaN columns are skipped safely."""
    records = []
    cluster_of = dict(
        zip(frame["company_id"].tolist(), np.asarray(labels, dtype=int).tolist())
    )
    for feat in features:
        series = pd.to_numeric(frame[feat], errors="coerce")
        observed = series.dropna()
        if len(observed) < 2:
            continue
        mu = float(observed.mean())
        sigma = float(observed.std(ddof=1))
        if sigma == 0 or not np.isfinite(sigma):
            continue  # constant feature: documented skip, no division by zero
        z = (series - mu) / sigma
        hits = frame[abs(z) > z_threshold]
        for idx in hits.index:
            records.append(
                {
                    "company_id": int(frame.at[idx, "company_id"]),
                    "ticker": str(frame.at[idx, "ticker"]),
                    "company_name": str(frame.at[idx, "company_name"]),
                    "fiscal_year": int(frame.at[idx, "year"]),
                    "feature": feat,
                    "observed_value": float(series.at[idx]),
                    "z_score": float(z.at[idx]),
                    "cluster_id": int(cluster_of[int(frame.at[idx, "company_id"])]),
                }
            )
    cols = [
        "company_id",
        "ticker",
        "company_name",
        "fiscal_year",
        "feature",
        "observed_value",
        "z_score",
        "cluster_id",
    ]
    out = pd.DataFrame(records, columns=cols)
    if len(out):
        out = out.sort_values(["feature", "ticker"]).reset_index(drop=True)
    return out


def portfolio_stats(
    frame: pd.DataFrame,
    labels: np.ndarray,
    features: list[str],
    outliers: pd.DataFrame | None = None,
    holdings: pd.DataFrame | None = None,
) -> dict:
    """Company-universe stats per cluster (unweighted).

    No portfolio holdings table exists in nifty100.db (verified 2026-10-09),
    so results are explicitly labelled unweighted universe statistics — never
    presented as invested-portfolio weights or returns. If a holdings frame
    with company_id+weight is supplied, per-cluster weight sums are added.
    """
    work = frame.copy()
    work["cluster_id"] = np.asarray(labels, dtype=int)
    total = len(work)
    by_cluster = {}
    for cid in sorted(work["cluster_id"].unique()):
        sub = work[work["cluster_id"] == cid]
        by_cluster[int(cid)] = {
            "company_count": len(sub),
            "share_pct": round(100.0 * len(sub) / total, 2) if total else 0.0,
            "tickers": sorted(sub["ticker"].tolist()),
        }
    out_count = 0 if outliers is None else len(outliers)
    result = {
        "universe_companies": int(total),
        "weighted": False,
        "note": (
            "No holdings/weights table in nifty100.db; "
            "figures are unweighted company-universe statistics."
        ),
        "by_cluster": by_cluster,
        "outlier_observations": out_count,
    }
    if holdings is not None:
        if "weight" not in holdings.columns or "company_id" not in holdings.columns:
            raise ValueError("holdings must carry company_id and weight columns")
        merged = work.merge(
            holdings[["company_id", "weight"]], on="company_id", how="left"
        )
        wsum = merged.groupby("cluster_id")["weight"].sum()
        for cid, w in wsum.items():
            by_cluster[int(cid)]["portfolio_weight"] = float(w)
        result["weighted"] = True
    return result


# ---------------------------------------------------------------------------
# End-to-end runner (used by scripts/run_clustering.py)
# ---------------------------------------------------------------------------


def run_clustering(
    db_path: str | Path | None = None,
    config_path: str | Path | None = None,
    run_id: str | None = None,
) -> dict:
    config = load_clustering_config(config_path)
    settings = clustering_settings(config)
    storage = config.get("storage", {})
    artifacts = PROJECT_ROOT / storage.get("artifacts_dir", "artifacts/clustering")

    frame, summary = load_company_features(db_path, config=config)
    prep = preprocess_features(
        frame,
        list(settings["feature_columns"]),
        settings.get("imputation_strategy", "median"),
    )
    return _finish_run(
        db_path, config, settings, storage, artifacts, frame, summary, prep, run_id
    )


def _finish_run(
    db_path, config, settings, storage, artifacts, frame, summary, prep, run_id
):
    retained = prep["retained_features"]
    elbow = elbow_analysis(
        prep["scaled"],
        max_k=int(settings.get("elbow_max_k", 10)),
        random_state=int(settings.get("random_state", 42)),
        n_init=int(settings.get("n_init", 10)),
        save_path=artifacts / "elbow.png",
    )
    model = fit_kmeans(
        prep["scaled"],
        n_clusters=int(settings.get("n_clusters", 5)),
        random_state=int(settings.get("random_state", 42)),
        n_init=int(settings.get("n_init", 10)),
        max_iter=int(settings.get("max_iter", 300)),
    )
    labels = np.asarray(model.labels_, dtype=int)
    profiles = cluster_profiles(frame, labels, retained)
    names = assign_cluster_names(profiles, retained)
    corr = correlation_heatmap(
        frame, retained, save_path=artifacts / "correlation_heatmap.png"
    )
    outliers = detect_outliers(
        frame,
        labels,
        retained,
        z_threshold=float(settings.get("outlier_z_threshold", 3.0)),
    )
    stats = portfolio_stats(frame, labels, retained, outliers)

    rid = run_id or datetime.now(UTC).strftime("run_%Y%m%d_%H%M%S")
    meta = save_results(
        db_path,
        rid,
        frame,
        labels,
        names,
        summary,
        retained,
        int(settings.get("random_state", 42)),
        float(model.inertia_),
        settings.get("imputation_strategy", "median"),
    )
    artifacts.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(artifacts / "cluster_profiles.csv", index=False)
    outliers.to_csv(artifacts / "outliers.csv", index=False)
    return {
        "run_id": rid,
        "meta": meta,
        "summary": summary,
        "prep": {
            "retained_features": retained,
            "removed_features": prep["removed_features"],
            "constant_features": prep["constant_features"],
            "missing_before": prep["missing_before"],
        },
        "cluster_sizes": profiles[["cluster_id", "company_count", "share_pct"]].to_dict(
            "records"
        ),
        "cluster_names": names,
        "stats": stats,
        "elbow": elbow,
        "corr_shape": list(corr.shape),
        "outlier_observations": len(outliers),
        "artifacts_dir": str(artifacts),
    }
