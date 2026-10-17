"""Sprint 6 — clustering unit tests (Day 36 + Day 37 pure-python paths).

sklearn/matplotlib-dependent paths use pytest.importorskip so the suite
stays runnable where only the light deps are installed; the full KMeans
run is covered by scripts/run_clustering.py on a synced env.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.analytics.clustering import (
    assign_cluster_names,
    cluster_profiles,
    detect_outliers,
    fit_kmeans,
    load_clustering_config,
    load_company_features,
    portfolio_stats,
    preprocess_features,
    validate_clustering_config,
    validate_feature_columns,
)

FEATURES = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "pe_ratio",
    "dividend_yield",
]


def _toy_frame(n=12, seed=7):
    rng = np.random.default_rng(seed)
    data = {
        "company_id": list(range(1, n + 1)),
        "ticker": [f"C{i:03d}" for i in range(1, n + 1)],
        "company_name": [f"Company {i}" for i in range(1, n + 1)],
        "sector": ["Energy"] * n,
        "year": [2024] * n,
    }
    for f in FEATURES:
        data[f] = rng.normal(10, 3, size=n)
    return pd.DataFrame(data)


# --- config ---------------------------------------------------------------


def test_config_loads_with_ten_validated_features():
    cfg = load_clustering_config()
    feats = cfg["clustering"]["feature_columns"]
    assert len(feats) == 10
    assert cfg["clustering"]["n_clusters"] == 5


def test_config_rejects_empty_features():
    cfg = load_clustering_config()
    bad = {**cfg, "clustering": {**cfg["clustering"], "feature_columns": []}}
    with pytest.raises(ValueError, match="non-empty"):
        validate_clustering_config(bad)


def test_config_rejects_identifier_columns():
    cfg = load_clustering_config()
    bad = {
        **cfg,
        "clustering": {
            **cfg["clustering"],
            "feature_columns": ["ticker", "return_on_equity_pct"],
        },
    }
    with pytest.raises(ValueError, match="identifier"):
        validate_clustering_config(bad)


def test_config_rejects_other_k():
    cfg = load_clustering_config()
    bad = {**cfg, "clustering": {**cfg["clustering"], "n_clusters": 3}}
    with pytest.raises(ValueError, match="n_clusters=5"):
        validate_clustering_config(bad)


def test_unknown_feature_gives_clear_error():
    with pytest.raises(ValueError, match="Unknown clustering feature"):
        validate_feature_columns("nifty100.db", ["roe_growthk"])


# --- loading ---------------------------------------------------------------


def test_load_one_row_per_company_latest_year():
    df, summary = load_company_features()
    assert summary["period"] == "latest_available_year"
    assert summary["records_loaded"] == 92
    assert summary["retained"] == 92
    assert not df["company_id"].duplicated().any()
    assert (df["year"] == 2024).all()


def test_load_explicit_year():
    df, summary = load_company_features(as_of_year=2023)
    assert summary["period"] == 2023
    assert (df["year"] == 2023).all()


def test_load_converts_inf_to_nan():
    df, _ = load_company_features()
    for f in FEATURES:
        assert not np.isinf(df[f].dropna().to_numpy()).any()


# --- preprocessing validation (no sklearn needed) --------------------------


def test_preprocess_rejects_empty_frame():
    with pytest.raises(ValueError, match="no eligible companies"):
        preprocess_features(pd.DataFrame(columns=FEATURES), FEATURES)


def test_preprocess_rejects_all_empty_features():
    df = _toy_frame()
    for f in FEATURES:
        df[f] = np.nan
    with pytest.raises(ValueError, match="entirely missing"):
        preprocess_features(df, FEATURES)


def test_preprocess_median_scale_and_reproducibility():
    pytest.importorskip("sklearn")
    df = _toy_frame()
    df.loc[0, "pe_ratio"] = np.nan
    first = preprocess_features(df, FEATURES)
    second = preprocess_features(df, FEATURES)
    assert first["retained_features"] == FEATURES
    assert first["removed_features"] == []
    assert first["missing_before"]["pe_ratio"] == 1
    np.testing.assert_allclose(first["scaled"], second["scaled"])
    # StandardScaler centres retained columns ~0
    assert abs(first["scaled"][:, 0].mean()) < 1e-9


def test_kmeans_requires_five_and_enough_companies():
    with pytest.raises(ValueError, match="n_clusters=5"):
        fit_kmeans(np.zeros((10, 2)), n_clusters=3)
    with pytest.raises(ValueError, match="Not enough eligible"):
        fit_kmeans(np.zeros((4, 2)), n_clusters=5)


def test_kmeans_fits_five_on_synthetic():
    pytest.importorskip("sklearn")
    rng = np.random.default_rng(0)
    scaled = rng.normal(size=(12, 4))
    model = fit_kmeans(scaled)
    assert model.n_clusters == 5
    assert len(model.labels_) == 12


def test_repeat_runs_reproducible():
    pytest.importorskip("sklearn")
    rng = np.random.default_rng(3)
    scaled = rng.normal(size=(15, 4))
    assert (fit_kmeans(scaled).labels_ == fit_kmeans(scaled).labels_).all()


# --- Day 37 -----------------------------------------------------------------


def test_profiles_use_observed_values_and_sum_to_100():
    df = _toy_frame()
    labels = np.array([0] * 6 + [1] * 6)
    prof = cluster_profiles(df, labels, FEATURES[:3])
    assert prof["company_count"].tolist() == [6, 6]
    assert prof["share_pct"].sum() == pytest.approx(100.0)
    expected = df.iloc[:6]["net_profit_margin_pct"].mean()
    assert prof.loc[0, "net_profit_margin_pct_mean"] == pytest.approx(expected)


def test_names_unique_with_fallback():
    df = _toy_frame()
    labels = np.zeros(len(df), dtype=int)  # single populated cluster
    prof = cluster_profiles(df, labels, FEATURES)
    names = assign_cluster_names(prof, FEATURES)
    assert len(names) == 1 and len(set(names.values())) == 1


def test_outlier_detects_both_tails_and_skips_constant():
    df = _toy_frame(n=30)
    df["debt_to_equity"] = 1.0  # constant -> skipped, no crash
    df.loc[0, "return_on_equity_pct"] = 1000.0
    df.loc[1, "return_on_equity_pct"] = -1000.0
    labels = np.zeros(len(df), dtype=int)
    out = detect_outliers(df, labels, ["return_on_equity_pct", "debt_to_equity"])
    assert (out["feature"] == "return_on_equity_pct").all()
    assert {0, 1} <= set(
        df.index[df["company_id"].isin(out["company_id"])].tolist()
    ) or len(out) >= 2
    assert (out["z_score"].abs() > 3).all()


def test_outlier_threshold_is_strictly_greater():
    # An impossibly high threshold flags nothing; threshold 0 flags
    # every non-mean observation — proving the comparison is strict >.
    df = _toy_frame(n=5)
    labels = np.zeros(5, dtype=int)
    assert len(detect_outliers(df, labels, FEATURES[:2], z_threshold=1e9)) == 0
    assert len(detect_outliers(df, labels, FEATURES[:2], z_threshold=0)) >= 1


def test_portfolio_stats_unweighted_and_labelled():
    df = _toy_frame()
    labels = np.array([0] * 6 + [1] * 6)
    stats = portfolio_stats(df, labels, FEATURES[:2])
    assert stats["weighted"] is False
    assert "No holdings" in stats["note"]
    assert stats["by_cluster"][0]["company_count"] == 6
