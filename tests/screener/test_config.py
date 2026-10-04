"""Unit tests — screener configuration loading & validation."""

import copy

import pytest
import yaml

from src.screener.engine import load_screener_config, validate_config


def _base_config():
    return load_screener_config()


# --- valid config ---


def test_valid_config_loads():
    cfg = _base_config()
    assert cfg["version"] == 1
    assert cfg["screening"]["observation"] == "latest_available_year"
    assert cfg["result_validation"]["min_companies"] == 5
    assert cfg["result_validation"]["max_companies"] == 50
    assert cfg["missing_value_policy"] == "fail"


def test_all_six_presets_defined():
    cfg = _base_config()
    for name in (
        "quality_compounder",
        "value_pick",
        "growth_accelerator",
        "dividend_champion",
        "debt_free_blue_chip",
        "turnaround_watch",
    ):
        assert name in cfg["presets"], f"preset '{name}' missing"
        assert isinstance(cfg["presets"][name]["filters"], list)
        assert len(cfg["presets"][name]["filters"]) > 0


def test_fifteen_metrics_defined():
    cfg = _base_config()
    assert len(cfg["metrics"]) >= 15
    for expected in (
        "roe",
        "net_profit_margin",
        "operating_profit_margin",
        "debt_to_equity",
        "interest_coverage_ratio",
        "asset_turnover",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield",
        "dividend_payout_ratio",
        "revenue_growth_5yr",
        "profit_growth_5yr",
        "eps_growth_5yr",
        "total_debt",
        "earnings_per_share",
    ):
        assert expected in cfg["metrics"], f"metric '{expected}' missing"


def test_operators_valid():
    cfg = _base_config()
    for op in cfg["operators"]:
        assert op in ("gt", "gte", "lt", "lte", "eq", "neq")


def test_debt_free_preset_does_not_waive_de():
    """Debt-free must hold even for financials (no silent waiver)."""
    cfg = _base_config()
    de_filters = [
        f
        for f in cfg["presets"]["debt_free_blue_chip"]["filters"]
        if f["metric"] == "debt_to_equity"
    ]
    assert de_filters, "debt_free_blue_chip must filter on debt_to_equity"
    assert all(f.get("apply_exception", True) is False for f in de_filters)


# --- invalid config ---


def test_malformed_yaml_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("presets: [unclosed\n  foo: ", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed screener YAML"):
        load_screener_config(bad)


def test_unknown_metric_raises():
    cfg = _base_config()
    bad = copy.deepcopy(cfg)
    bad["presets"]["quality_compounder"]["filters"][0]["metric"] = "roe_growthk"
    with pytest.raises(ValueError, match="Unknown screener metric 'roe_growthk'"):
        validate_config(bad)


def test_invalid_operator_raises():
    cfg = _base_config()
    bad = copy.deepcopy(cfg)
    bad["presets"]["quality_compounder"]["filters"][0]["operator"] = "approx"
    with pytest.raises(ValueError, match="Unknown screener operator"):
        validate_config(bad)


def test_missing_threshold_raises():
    cfg = _base_config()
    bad = copy.deepcopy(cfg)
    del bad["presets"]["quality_compounder"]["filters"][0]["value"]
    with pytest.raises(ValueError, match="missing 'value'"):
        validate_config(bad)


def test_invalid_threshold_type_raises():
    cfg = _base_config()
    for bad_value in ("high", None, True, float("nan")):
        bad = copy.deepcopy(cfg)
        bad["presets"]["quality_compounder"]["filters"][0]["value"] = bad_value
        with pytest.raises(ValueError, match="[Tt]hreshold|numeric|finite"):
            validate_config(bad)


def test_invalid_preset_structure_raises():
    cfg = _base_config()
    bad = copy.deepcopy(cfg)
    bad["presets"]["quality_compounder"]["filters"] = []
    with pytest.raises(ValueError, match="non-empty 'filters'"):
        validate_config(bad)


def test_missing_config_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="Screener config not found"):
        load_screener_config(tmp_path / "does_not_exist.yaml")


def test_unknown_preset_error_message():
    from src.screener.engine import get_preset

    cfg = _base_config()
    with pytest.raises(ValueError, match="Unknown screener preset 'nope'"):
        get_preset(cfg, "nope")
