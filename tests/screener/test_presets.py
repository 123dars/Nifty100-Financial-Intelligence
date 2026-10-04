"""Preset tests — all six presets on the project dataset (nifty100.db)."""

import pytest

from src.screener.engine import (
    get_preset,
    load_screener_config,
    resolve_metric,
    run_preset,
    validate_result_count,
)

PRESETS = [
    "quality_compounder",
    "value_pick",
    "growth_accelerator",
    "dividend_champion",
    "debt_free_blue_chip",
    "turnaround_watch",
]


@pytest.fixture(scope="module")
def cfg():
    return load_screener_config()


@pytest.fixture(scope="module")
def results():
    return {name: run_preset(name) for name in PRESETS}


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_exists_and_loads_from_yaml(cfg, preset):
    p = get_preset(cfg, preset)
    assert isinstance(p["filters"], list) and len(p["filters"]) > 0


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_metrics_exist(cfg, preset):
    for flt in get_preset(cfg, preset)["filters"]:
        resolve_metric(cfg, flt["metric"])  # raises with clear message if bad


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_result_schema(results, preset):
    res = results[preset]
    assert res["preset_name"] == preset
    assert res["screening_year"] == 2024
    assert res["total_input_companies"] == 92
    assert res["matched_count"] == len(res["matched_companies"])
    assert isinstance(res["applied_filters"], list)
    for company in res["matched_companies"]:
        for key in ("ticker", "company_name", "sector", "screening_year"):
            assert key in company, f"company missing '{key}'"
        assert company["screening_year"] == 2024


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_no_duplicate_companies(results, preset):
    tickers = [c["ticker"] for c in results[preset]["matched_companies"]]
    assert len(tickers) == len(set(tickers))


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_deterministic(preset):
    first = [c["ticker"] for c in run_preset(preset)["matched_companies"]]
    second = [c["ticker"] for c in run_preset(preset)["matched_companies"]]
    assert first == second
    assert first == sorted(first)  # deterministic ticker ordering


@pytest.mark.parametrize("preset", PRESETS)
def test_preset_count_within_5_and_50(cfg, results, preset, capsys=None):
    res = results[preset]
    ok, msg = validate_result_count(res["matched_count"], preset, cfg)
    assert ok, msg
    assert 5 <= res["matched_count"] <= 50


def test_preset_count_report(results):
    """Human-readable report (also serves as the required count table)."""
    lines = [
        f"{name:22s} -> {results[name]['matched_count']}"
        for name in PRESETS
    ]
    report = "\n".join(lines)
    assert all(5 <= results[n]["matched_count"] <= 50 for n in PRESETS), report
