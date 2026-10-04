"""Unit tests — result-count validation (never relax/truncate, only report)."""

from src.screener.engine import load_screener_config, validate_result_count


def test_below_minimum_fails():
    cfg = load_screener_config()
    ok, msg = validate_result_count(3, "value_pick", cfg)
    assert ok is False
    assert "value_pick" in msg and "3" in msg


def test_above_maximum_fails():
    cfg = load_screener_config()
    ok, msg = validate_result_count(51, "quality_compounder", cfg)
    assert ok is False
    assert "quality_compounder" in msg and "51" in msg


def test_boundaries_pass():
    cfg = load_screener_config()
    for n in (5, 6, 25, 49, 50):
        ok, _ = validate_result_count(n, "growth_accelerator", cfg)
        assert ok is True


def test_limits_come_from_config():
    cfg = load_screener_config()
    assert cfg["result_validation"]["min_companies"] == 5
    assert cfg["result_validation"]["max_companies"] == 50
