"""Sprint 3 — Generic Screener Engine.

Consumes Sprint 2 calculated metrics (``financial_ratios`` + ``financial_ratios_source``)
and applies configurable metric filters from ``config/screener_config.yaml``.

Data flow:
    financial_ratios (Sprint 2, computed)
      + financial_ratios_source (vendor PE/PB/yield)
      + companies (sector for D/E exception)
      + profitandloss.interest (for ICR edge cases)
        -> one screening observation per company (latest available year)
        -> AND filters -> preset company set

Missing-value policy: missing metric = filter FAILS (NULL != 0).
The engine is read-only w.r.t. source data (SELECT only).
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "screener_config.yaml"
DEFAULT_DB_PATH = PROJECT_ROOT / "nifty100.db"

SUPPORTED_OPERATORS = ("gt", "gte", "lt", "lte", "eq", "neq")
# Symbol aliases accepted in YAML for convenience.
OPERATOR_ALIASES = {
    ">": "gt",
    ">=": "gte",
    "<": "lt",
    "<=": "lte",
    "==": "eq",
    "=": "eq",
    "!=": "neq",
    "<>": "neq",
}


# ---------------------------------------------------------------------------
# Config loading / validation
# ---------------------------------------------------------------------------


def load_screener_config(path: str | Path | None = None) -> dict:
    """Load screener YAML config. Raises FileNotFoundError / ValueError on problems."""
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Screener config not found: {cfg_path}")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ValueError(f"Malformed screener YAML at {cfg_path}: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError(f"Malformed screener YAML at {cfg_path}: top level must be a mapping")
    return validate_config(config)


def validate_config(config: dict) -> dict:
    """Validate config structure; return it unchanged. Raises ValueError with clear messages."""
    if "version" not in config:
        raise ValueError("Invalid screener config: missing 'version'")
    screening = config.get("screening")
    if not isinstance(screening, dict) or "observation" not in screening:
        raise ValueError("Invalid screener config: 'screening.observation' is required")
    if screening["observation"] not in ("latest_available_year",):
        raise ValueError(
            f"Invalid screener config: unknown observation "
            f"'{screening['observation']}'. Expected one of: ['latest_available_year']"
        )

    rv = config.get("result_validation", {})
    if "min_companies" not in rv or "max_companies" not in rv:
        raise ValueError(
            "Invalid screener config: 'result_validation.min_companies/max_companies' required"
        )

    policy = config.get("missing_value_policy", "fail")
    if policy not in ("fail",):
        raise ValueError(
            f"Invalid screener config: unknown missing_value_policy '{policy}'. "
            "Expected one of: ['fail']"
        )

    metrics = config.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise ValueError("Invalid screener config: 'metrics' must be a non-empty mapping")
    for name, spec in metrics.items():
        if not isinstance(spec, dict):
            raise ValueError(f"Invalid screener config: metric '{name}' must be a mapping")
        for key in ("source_table", "source_column"):
            if key not in spec:
                raise ValueError(f"Invalid screener config: metric '{name}' missing '{key}'")

    operators = config.get("operators", [])
    for op in operators:
        canon = OPERATOR_ALIASES.get(op, op)
        if canon not in SUPPORTED_OPERATORS:
            raise ValueError(
                f"Invalid screener config: unknown operator '{op}'. "
                f"Expected one of: {list(SUPPORTED_OPERATORS)}"
            )

    presets = config.get("presets")
    if not isinstance(presets, dict) or not presets:
        raise ValueError("Invalid screener config: 'presets' must be a non-empty mapping")
    for pname, preset in presets.items():
        if not isinstance(preset, dict):
            raise ValueError(f"Invalid screener config: preset '{pname}' must be a mapping")
        filters = preset.get("filters")
        if not isinstance(filters, list) or not filters:
            raise ValueError(f"Invalid screener config: preset '{pname}' needs a non-empty 'filters' list")
        for i, flt in enumerate(filters):
            if not isinstance(flt, dict):
                raise ValueError(f"Invalid screener config: preset '{pname}' filter #{i} must be a mapping")
            for key in ("metric", "operator", "value"):
                if key not in flt:
                    raise ValueError(
                        f"Invalid screener config: preset '{pname}' filter #{i} missing '{key}'"
                    )
            if flt["metric"] not in metrics:
                raise ValueError(
                    f"Unknown screener metric '{flt['metric']}' in preset '{pname}'. "
                    f"Expected one of: {sorted(metrics)}"
                )
            canon = OPERATOR_ALIASES.get(flt["operator"], flt["operator"])
            if canon not in SUPPORTED_OPERATORS:
                raise ValueError(
                    f"Unknown screener operator '{flt['operator']}' in preset '{pname}'. "
                    f"Expected one of: {list(SUPPORTED_OPERATORS)}"
                )
            val = flt["value"]
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(
                    f"Invalid screener threshold for '{flt['metric']}' in preset '{pname}': "
                    f"{val!r} (must be numeric)"
                )
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                raise ValueError(
                    f"Invalid screener threshold for '{flt['metric']}' in preset '{pname}': "
                    f"{val!r} (must be a finite number)"
                )
            if "apply_exception" in flt and not isinstance(flt["apply_exception"], bool):
                raise ValueError(
                    f"Invalid screener config: preset '{pname}' filter #{i} "
                    f"'apply_exception' must be boolean"
                )
    return config


# ---------------------------------------------------------------------------
# Metric / operator primitives
# ---------------------------------------------------------------------------


def resolve_metric(config: dict, metric_name: str) -> dict:
    """Return the metric spec for ``metric_name`` or raise a clear error."""
    metrics = config.get("metrics", {})
    if metric_name not in metrics:
        raise ValueError(
            f"Unknown screener metric '{metric_name}'. Expected one of: {sorted(metrics)}"
        )
    return metrics[metric_name]


def canonical_operator(operator: str) -> str:
    """Normalise operator name/alias -> canonical name, or raise."""
    canon = OPERATOR_ALIASES.get(operator, operator)
    if canon not in SUPPORTED_OPERATORS:
        raise ValueError(
            f"Unknown screener operator '{operator}'. Expected one of: {list(SUPPORTED_OPERATORS)}"
        )
    return canon


def is_missing(value: Any) -> bool:
    """NULL/NaN/inf/-inf/non-numeric-string all count as missing (fail the filter).

    NOTE: +inf produced by the ICR debt-free policy is handled *before* this
    check (effective ICR), so genuine stored inf/-inf is treated as missing.
    """
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        f = float(value)
        return math.isnan(f) or math.isinf(f)
    if isinstance(value, str):
        s = value.strip()
        if s == "" or s.lower() in ("nan", "none", "null", "inf", "+inf", "-inf"):
            return True
        try:
            f = float(s)
        except ValueError:
            return True
        return math.isnan(f) or math.isinf(f)
    return True


def evaluate_operator(operator: str, actual: float, expected: float) -> bool:
    """Centralised comparison. Caller guarantees finite numerics."""
    op = canonical_operator(operator)
    if op == "gt":
        return actual > expected
    if op == "gte":
        return actual >= expected
    if op == "lt":
        return actual < expected
    if op == "lte":
        return actual <= expected
    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    raise ValueError(f"Unknown screener operator '{operator}'")  # pragma: no cover


def apply_single_filter(value: Any, operator: str, threshold: float) -> bool:
    """Evaluate one ``value <op> threshold``. Missing/invalid value -> False."""
    if is_missing(value):
        return False
    try:
        actual = float(value)
    except (TypeError, ValueError):
        return False
    if math.isnan(actual) or math.isinf(actual):
        return False
    return evaluate_operator(operator, actual, float(threshold))


# ---------------------------------------------------------------------------
# Exceptions: Financial D/E + debt-free ICR
# ---------------------------------------------------------------------------


def is_financial_sector(sector: Any, excluded_sectors: list) -> bool:
    """Config-driven sector match (case-insensitive). Non-string -> False."""
    if not isinstance(sector, str):
        return False
    s = sector.strip().lower()
    return any(s == str(e).strip().lower() for e in (excluded_sectors or []))


def is_debt_free(total_debt: Any, debt_zero_threshold: float = 0) -> bool:
    """Authoritative debt-free signal. NULL debt is NEVER debt-free."""
    if is_missing(total_debt):
        return False
    try:
        return float(total_debt) <= float(debt_zero_threshold)
    except (TypeError, ValueError):
        return False


def effective_interest_coverage(row: dict, config: dict) -> float | None:
    """Apply the configured ICR debt-free policy for one company observation.

    Uses ``total_debt_cr`` (preferred over D/E == 0) and ``interest_expense``::

        interest is missing/NaN        -> None (missing -> filter fails)
        interest == 0                   -> +inf (no division by zero)
        interest < 0 or non-finite      -> +inf (per negative_interest_policy)
        debt == 0 and interest == 0     -> +inf (Case A)
        debt == 0 and interest > 0      -> stored ICR (Case B, normal)
        otherwise                       -> stored ICR (may itself be missing)

    Stored inf/-inf/NaN/NULL counts as missing (-> None), *except* the +inf
    produced here, which passes any positive ICR threshold.
    """
    policy_holder = (config.get("exceptions", {}) or {}).get("interest_coverage_ratio", {}) or {}
    debt_free_cfg = (policy_holder.get("debt_free_policy", {}) or {})
    enabled = debt_free_cfg.get("enabled", True)
    _threshold = debt_free_cfg.get("debt_zero_threshold", 0)  # documented; detection is == 0

    interest = row.get("interest_expense")
    stored = row.get("interest_coverage_ratio")

    # Missing interest -> cannot evaluate (do NOT infer debt-free).
    if interest is None:
        return None
    try:
        # pandas NaN check without importing pandas here
        if isinstance(interest, float) and math.isnan(interest):
            return None
        interest_f = float(interest)
    except (TypeError, ValueError):
        return None

    if math.isnan(interest_f):
        return None
    if interest_f == 0:
        return math.inf if enabled else None
    if math.isinf(interest_f) or interest_f < 0:
        # negative/invalid interest: configured policy, not silent zeroing.
        return math.inf if enabled else None

    # Positive interest: normal path — use stored ICR (covers Case B).
    if is_missing(stored):
        return None
    try:
        return float(stored)
    except (TypeError, ValueError):
        return None


def should_waive_de_filter(sector: Any, config: dict, flt: dict | None = None) -> bool:
    """True when the Financial D/E exception waives the D/E filter for this row.

    Waiver is config-driven (``exceptions.debt_to_equity``) and can be opted
    out per filter via ``apply_exception: false`` — used by the debt-free
    preset, where "debt-free" must hold even for financial companies.
    """
    if flt is not None and flt.get("apply_exception", True) is False:
        return False
    exc = ((config.get("exceptions", {}) or {}).get("debt_to_equity", {}) or {})
    if not exc.get("enabled", False):
        return False
    return is_financial_sector(sector, exc.get("excluded_sectors", []))


# ---------------------------------------------------------------------------
# Data loading — one observation per company (latest available year)
# ---------------------------------------------------------------------------


def _table_columns(conn: sqlite3.Connection, table: str) -> set:
    return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()}


def select_screening_observation(rows: list[dict]) -> list[dict]:
    """Keep the latest-year row per company_id (deterministic; no duplicates).

    Rows must contain ``company_id`` and ``year``. Ties are impossible
    (one row per company-year); output sorted by company_id for determinism.
    """
    latest: dict[Any, dict] = {}
    for r in rows:
        cid = r.get("company_id")
        y = r.get("year")
        if cid is None or y is None:
            continue
        if cid not in latest or y > latest[cid].get("year"):
            latest[cid] = r
    return [latest[cid] for cid in sorted(latest)]


def load_screening_frame(
    db_path: str | Path | None = None, config: dict | None = None
) -> list[dict]:
    """Load denormalised screening observations (SELECT only — never mutates data).

    One dict per company at its latest ``financial_ratios.year``, with keys:
    company_id, ticker, company_name, sector, industry, screening_year,
    <each metric config name>, interest_expense, total_debt_cr (via metric).
    """
    if config is None:
        config = load_screener_config()
    db = str(db_path) if db_path else str(DEFAULT_DB_PATH)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for required in ("companies", "financial_ratios"):
            if required not in tables:
                raise ValueError(f"Missing required table '{required}' in {db}")
        has_source = "financial_ratios_source" in tables
        has_pl = "profitandloss" in tables

        # Latest year per company from the Sprint 2 output (authoritative grain).
        latest_rows = conn.execute(
            "SELECT company_id, MAX(year) AS max_year FROM financial_ratios GROUP BY company_id"
        ).fetchall()
        latest = {r["company_id"]: r["max_year"] for r in latest_rows}

        metrics = config.get("metrics", {})
        # Validate source columns exist before querying (clear error, not KeyError).
        fr_cols = _table_columns(conn, "financial_ratios")
        src_cols = _table_columns(conn, "financial_ratios_source") if has_source else set()
        pl_cols = _table_columns(conn, "profitandloss") if has_pl else set()
        for mname, spec in metrics.items():
            tbl, col = spec["source_table"], spec["source_column"]
            if tbl == "financial_ratios" and col not in fr_cols:
                raise ValueError(
                    f"Metric '{mname}' maps to missing column "
                    f"financial_ratios.{col} in {db}"
                )
            if tbl == "profitandloss":
                if not has_pl:
                    raise ValueError(f"Metric '{mname}' needs table 'profitandloss'")
                if col not in pl_cols:
                    raise ValueError(f"Metric '{mname}' maps to missing column profitandloss.{col}")
            if tbl == "computed":
                pass
            if tbl == "financial_ratios_source":
                if not has_source:
                    raise ValueError(
                        f"Metric '{mname}' needs table 'financial_ratios_source' (missing in {db})"
                    )
                if col not in src_cols:
                    raise ValueError(
                        f"Metric '{mname}' maps to missing column "
                        f"financial_ratios_source.{col} in {db}"
                    )
        if has_pl and "interest" not in pl_cols:
            raise ValueError(f"Missing required column profitandloss.interest in {db}")

        observations: list[dict] = []
        for cid in sorted(latest):
            year = latest[cid]
            comp = conn.execute(
                "SELECT company_id, ticker, company_name, sector, industry "
                "FROM companies WHERE company_id = ?",
                (cid,),
            ).fetchone()
            if comp is None:
                continue
            fr = conn.execute(
                "SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?",
                (cid, year),
            ).fetchone()
            src = None
            if has_source:
                src = conn.execute(
                    "SELECT * FROM financial_ratios_source WHERE company_id = ? AND year = ?",
                    (cid, year),
                ).fetchone()
            interest_expense = None
            if has_pl:
                pl = conn.execute(
                    "SELECT * FROM profitandloss WHERE company_id = ? AND year = ?",
                    (cid, year),
                ).fetchone()
                interest_expense = pl["interest"] if pl else None
            else:
                pl = None

            fr_d = dict(fr) if fr else {}
            src_d = dict(src) if src else {}
            row: dict[str, Any] = {
                "company_id": cid,
                "ticker": comp["ticker"],
                "company_name": comp["company_name"],
                "sector": comp["sector"],
                "industry": comp["industry"],
                "screening_year": year,
                "interest_expense": interest_expense,
            }
            pl_d = dict(pl) if pl else {}
            for mname, spec in metrics.items():
                tbl = spec["source_table"]
                col = spec["source_column"]
                if tbl == "financial_ratios":
                    row[mname] = fr_d.get(col)
                elif tbl == "financial_ratios_source":
                    row[mname] = src_d.get(col) if src_d else None
                elif tbl == "profitandloss":
                    row[mname] = pl_d.get(col) if pl_d else None
                elif tbl == "computed":
                    if col == "market_cap":
                        pe = src_d.get("pe_ratio") if src_d else None
                        net_profit = pl_d.get("net_profit") if pl_d else None
                        if pe is not None and net_profit is not None:
                            row[mname] = pe * net_profit
                        else:
                            row[mname] = None
                    elif col == "revenue_cagr_3yr":
                        pl_past = conn.execute("SELECT sales FROM profitandloss WHERE company_id = ? AND year = ?", (cid, year - 3)).fetchone()
                        sales_now = pl_d.get("sales")
                        sales_past = pl_past["sales"] if pl_past else None
                        if sales_now and sales_past and sales_past > 0:
                            row[mname] = ((sales_now / sales_past) ** (1/3) - 1) * 100
                        else:
                            row[mname] = None
                    elif col == "de_declining_yoy":
                        fr_past = conn.execute("SELECT debt_to_equity FROM financial_ratios WHERE company_id = ? AND year = ?", (cid, year - 1)).fetchone()
                        de_now = fr_d.get("debt_to_equity")
                        de_past = fr_past["debt_to_equity"] if fr_past else None
                        if de_now is not None and de_past is not None:
                            row[mname] = 1 if de_now < de_past else 0
                        else:
                            row[mname] = None
                else:
                    raise ValueError(
                        f"Metric '{mname}' has unsupported source_table "
                        f"'{tbl}'"
                    )
            observations.append(row)
        return observations
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def row_passes_filters(row: dict, filters: list[dict], config: dict) -> tuple[bool, list[str]]:
    """Evaluate AND-filters for one row. Returns (passed, failed_metric_names).

    - D/E filter is waived for configured financial sectors (exception).
    - ICR uses the effective (policy-adjusted) value, so debt-free/zero-interest
      rows pass positive thresholds instead of crashing or failing.
    """
    failed: list[str] = []
    for flt in filters:
        metric, operator, threshold = flt["metric"], flt["operator"], flt["value"]
        resolve_metric(config, metric)  # clear error on unknown metric
        if metric == "debt_to_equity" and should_waive_de_filter(
            row.get("sector"), config, flt
        ):
            continue
        if metric == "interest_coverage_ratio":
            value = effective_interest_coverage(row, config)
            # effective inf must NOT be treated as missing: compare directly.
            if value is None:
                failed.append(metric)
                continue
            if isinstance(value, float) and math.isinf(value) and value > 0:
                if not evaluate_operator(operator, value, float(threshold)):
                    failed.append(metric)
                continue
        else:
            value = row.get(metric)
        if not apply_single_filter(value, operator, threshold):
            failed.append(metric)
    return (len(failed) == 0), failed


def apply_filters(
    rows: list[dict], filters: list[dict], config: dict, debug: bool = False
) -> tuple[list[dict], dict]:
    """Apply AND-filters to all rows. Returns (matched_rows, debug_info)."""
    matched: list[dict] = []
    remaining_by_filter: list[dict] = []
    candidates = list(rows)
    exceptions_applied = 0
    for flt in filters:
        survivors: list[dict] = []
        for row in candidates:
            ok, _ = row_passes_filters(row, [flt], config)
            if ok:
                survivors.append(row)
            elif flt["metric"] == "debt_to_equity" and should_waive_de_filter(
                row.get("sector"), config, flt
            ):
                survivors.append(row)  # unreachable (waived inside), kept for clarity
        # Count waivers for reporting: financial rows that would otherwise fail D/E.
        if flt["metric"] == "debt_to_equity":
            for row in candidates:
                if should_waive_de_filter(row.get("sector"), config, flt):
                    exceptions_applied += 1
        remaining_by_filter.append(
            {"filter": flt, "remaining": len(survivors), "removed": len(candidates) - len(survivors)}
        )
        candidates = survivors
    matched = sorted(candidates, key=lambda r: (r.get("ticker") or "", r.get("company_id") or 0))
    debug_info = {
        "input_count": len(rows),
        "filter_steps": remaining_by_filter,
        "exceptions_applied": exceptions_applied,
        "final_count": len(matched),
    }
    if debug:  # pragma: no cover - manual debugging aid
        print(f"Input: {len(rows)}")
        for step in remaining_by_filter:
            f = step["filter"]
            print(f"{f['metric']} {f['operator']} {f['value']} -> Remaining: {step['remaining']}")
    return matched, debug_info


# ---------------------------------------------------------------------------
# Presets + result validation
# ---------------------------------------------------------------------------


def get_preset(config: dict, preset_name: str) -> dict:
    """Fetch preset or raise a clear error."""
    presets = config.get("presets", {})
    if preset_name not in presets:
        raise ValueError(
            f"Unknown screener preset '{preset_name}'. Expected one of: {sorted(presets)}"
        )
    return presets[preset_name]


def validate_result_count(
    matched_count: int, preset_name: str, config: dict
) -> tuple[bool, str]:
    """Check  min <= count <= max. Returns (passed, message); never truncates."""
    rv = config.get("result_validation", {})
    lo, hi = rv.get("min_companies", 5), rv.get("max_companies", 50)
    if matched_count < lo or matched_count > hi:
        return False, (
            f"Preset '{preset_name}' returned {matched_count} companies. "
            f"Expected between {lo} and {hi}."
        )
    return True, (
        f"Preset '{preset_name}' returned {matched_count} companies "
        f"(within {lo}–{hi})."
    )


def screen(
    preset_name: str | None = None,
    filters: list[dict] | None = None,
    db_path: str | Path | None = None,
    config: dict | None = None,
    debug: bool = False,
) -> dict:
    """Run one preset (by name) or an ad-hoc filter list. Returns structured result.

    Result keys: preset_name, screening_year, total_input_companies,
    matched_companies (list of dicts), matched_count, applied_filters,
    exceptions_applied, debug (when requested).
    """
    if config is None:
        config = load_screener_config()
    if preset_name is not None:
        preset = get_preset(config, preset_name)
        active_filters = preset["filters"]
        label = preset_name
    elif filters is not None:
        active_filters = filters
        label = "adhoc"
    else:
        raise ValueError("screen() requires preset_name or filters")

    rows = load_screening_frame(db_path, config)
    total = len(rows)
    # De-duplicate defensively (grain guarantees uniqueness already).
    seen, unique = set(), []
    for r in rows:
        if r.get("company_id") not in seen:
            seen.add(r.get("company_id"))
            unique.append(r)
    rows = unique

    matched, debug_info = apply_filters(rows, active_filters, config, debug=debug)
    years = [r.get("screening_year") for r in rows if r.get("screening_year") is not None]
    screening_year = max(years) if years else None

    metric_names = sorted({f["metric"] for f in active_filters})
    matched_companies = [
        {
            "company_id": r.get("company_id"),
            "ticker": r.get("ticker"),
            "company_name": r.get("company_name"),
            "sector": r.get("sector"),
            "industry": r.get("industry"),
            "screening_year": r.get("screening_year"),
            **{m: r.get(m) for m in metric_names},
        }
        for r in matched
    ]
    return {
        "preset_name": label,
        "screening_year": screening_year,
        "total_input_companies": total,
        "matched_companies": matched_companies,
        "matched_count": len(matched_companies),
        "applied_filters": active_filters,
        "exceptions_applied": debug_info.get("exceptions_applied", 0),
        "debug_info": debug_info if debug else None,
    }


def run_preset(
    preset_name: str,
    db_path: str | Path | None = None,
    config_path: str | Path | None = None,
    debug: bool = False,
) -> dict:
    """Load config from YAML and run one preset (primary entry point)."""
    config = load_screener_config(config_path)
    return screen(preset_name=preset_name, db_path=db_path, config=config, debug=debug)


import sqlite3
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from src.screener.engine import run_preset

def get_raw_data(db_path):
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        c.company_id, c.ticker, c.company_name, c.sector,
        f.year,
        f.return_on_equity_pct as roe,
        f.net_profit_margin_pct as npm,
        f.debt_to_equity as de,
        f.interest_coverage as icr,
        f.revenue_cagr_5yr as rev_cagr,
        f.pat_cagr_5yr as pat_cagr,
        f.free_cash_flow_cr as fcf,
        p.operating_profit, p.other_income, p.net_profit, p.sales,
        b.equity, b.reserves, b.borrowings,
        cf.operating_cash_flow as cfo,
        cf.investing_cash_flow as cfi
    FROM companies c
    JOIN financial_ratios f ON c.company_id = f.company_id
    LEFT JOIN profitandloss p ON c.company_id = p.company_id AND f.year = p.year
    LEFT JOIN balancesheet b ON c.company_id = b.company_id AND f.year = b.year
    LEFT JOIN cashflow cf ON c.company_id = cf.company_id AND f.year = cf.year
    """
    df = pd.read_sql_query(query, conn)
    
    # Get year-5 FCF for FCF CAGR
    query_past = """
    SELECT c.company_id, f.year + 5 as year, f.free_cash_flow_cr as fcf_past
    FROM companies c
    JOIN financial_ratios f ON c.company_id = f.company_id
    """
    df_past = pd.read_sql_query(query_past, conn)
    
    conn.close()
    
    df = df.merge(df_past, on=['company_id', 'year'], how='left')
    return df

def calculate_composite_score(df):
    # Filter to latest year (2024)
    latest_year = df['year'].max()
    df = df[df['year'] == latest_year].copy()
    
    for c in ['operating_profit', 'other_income', 'equity', 'reserves', 'borrowings', 'net_profit', 'cfo']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        
    # Calculate ROCE
    ebit = df['operating_profit'].fillna(0) + df['other_income'].fillna(0)
    capital_employed = df['equity'].fillna(0) + df['reserves'].fillna(0) + df['borrowings'].fillna(0)
    df['roce'] = np.where(capital_employed > 0, ebit / capital_employed * 100, np.nan)
    
    # Calculate CFO/PAT
    df['cfo_pat'] = np.where(df['net_profit'] != 0, df['cfo'] / df['net_profit'], np.nan)
    
    def fcf_cagr(row):
        f1 = row['fcf_past']
        f5 = row['fcf']
        try:
            f1 = float(f1)
            f5 = float(f5)
            if pd.isna(f1) or pd.isna(f5) or f1 <= 0 or (f5 / f1) <= 0:
                return np.nan
            return ((f5 / f1) ** (1/5) - 1) * 100
        except:
            return np.nan
            
    df['fcf_cagr'] = df.apply(fcf_cagr, axis=1)
    df['fcf'] = pd.to_numeric(df['fcf'], errors='coerce')
    df['fcf_positive_flag'] = np.where(df['fcf'] > 0, 100, 0)
    
    metrics = {
        'roe': 0.15,
        'roce': 0.10,
        'npm': 0.10,
        'fcf_cagr': 0.15,
        'cfo_pat': 0.10,
        'rev_cagr': 0.10,
        'pat_cagr': 0.10,
        'de': 0.10,
        'icr': 0.05
    }
    
    for m in metrics:
        df[m] = pd.to_numeric(df[m], errors='coerce')
    
    df['composite_score'] = 0.0
    df['composite_score'] += df['fcf_positive_flag'] * 0.05
    
    for sector, group in df.groupby('sector'):
        for m, weight in metrics.items():
            vals = group[m].copy()
            # drop nans for quantile calculation
            v_clean = vals.dropna().astype(float)
            if v_clean.empty:
                continue
            p10 = v_clean.quantile(0.10)
            p90 = v_clean.quantile(0.90)
            vals = vals.clip(lower=p10, upper=p90)
            
            vmin = vals.min()
            vmax = vals.max()
            if vmax > vmin:
                scaled = (vals - vmin) / (vmax - vmin) * 100
            else:
                scaled = pd.Series(50.0, index=vals.index)
                
            if m == 'de':
                scaled = 100 - scaled
                
            scaled = scaled.fillna(0)
            df.loc[group.index, 'composite_score'] += scaled * weight

    return df

def generate_excel():
    db_path = 'nifty100.db'
    df_raw = get_raw_data(db_path)
    df_scored = calculate_composite_score(df_raw)
    
    conn = sqlite3.connect(db_path)
    for idx, row in df_scored.iterrows():
        try:
            val = float(row['composite_score'])
            if pd.isna(val):
                val = 0.0
            conn.execute("UPDATE financial_ratios SET composite_quality_score = ? WHERE company_id = ? AND year = ?",
                         (val, int(row['company_id']), int(row['year'])))
        except:
            pass
    conn.commit()
    conn.close()
    
    with open('config/screener_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    import xlsxwriter
    writer = pd.ExcelWriter('output/screener_output.xlsx', engine='xlsxwriter')
    workbook = writer.book
    
    green_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
    red_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
    
    for preset_name, preset in config['presets'].items():
        res = run_preset(preset_name, db_path=db_path)
        matched = res['matched_companies']
        if not matched:
            continue
            
        df_preset = pd.DataFrame(matched)
        
        # Merge composite score
        df_preset = df_preset.merge(df_scored[['company_id', 'composite_score']], on='company_id', how='left')
        df_preset = df_preset.sort_values('composite_score', ascending=False)
        
        sheet_name = preset_name[:31]
        df_preset.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        
        # Format columns based on filters
        for flt in preset['filters']:
            metric = flt['metric']
            op = flt['operator']
            val = flt['value']
            
            if metric not in df_preset.columns:
                continue
                
            col_idx = df_preset.columns.get_loc(metric)
            col_letter = xlsxwriter.utility.xl_col_to_name(col_idx)
            
            op_map = {
                'gt': '>', 'gte': '>=',
                'lt': '<', 'lte': '<=',
                'eq': '==', 'neq': '!='
            }
            if op in op_map:
                xl_op = op_map[op]
                worksheet.conditional_format(f'{col_letter}2:{col_letter}{len(df_preset)+1}', {
                    'type': 'cell', 'criteria': xl_op, 'value': val, 'format': green_format
                })
                inverse_op = {
                    '>': '<=', '>=': '<',
                    '<': '>=', '<=': '>',
                    '==': '!=', '!=': '=='
                }[xl_op]
                worksheet.conditional_format(f'{col_letter}2:{col_letter}{len(df_preset)+1}', {
                    'type': 'cell', 'criteria': inverse_op, 'value': val, 'format': red_format
                })
                
    writer.close()
    print("Screener Excel generated!")

if __name__ == '__main__':
    generate_excel()
