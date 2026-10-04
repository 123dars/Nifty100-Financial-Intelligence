# N100 Financial Intelligence Platform

A production-oriented financial data engineering and analytics platform for the **Nifty 100**, designed to transform raw financial datasets into a validated SQLite database for financial analysis, screening, reporting, and downstream analytics.

## Project Overview

The N100 Financial Intelligence Platform processes financial and market datasets for **92 Nifty 100 companies**.

The platform covers:

* Company master data
* Sector and industry information
* Profit & Loss
* Balance Sheet
* Cash Flow
* Financial Ratios
* Stock Prices
* Annual Reports
* Pros & Cons
* Peer Groups

The project follows an ETL and data-quality workflow:

```text
Raw Excel Files
       │
       ▼
Data Cleaning & Standardization
       │
       ▼
Processed CSV / Parquet Data
       │
       ▼
Data Validation
       │
       ▼
SQLite Database
       │
       ▼
Testing & Exploratory SQL
       │
       ▼
Final QA
```

---

# Sprint 1 — Data Foundation

## Sprint Objective

Build and validate the data foundation required for the N100 Financial Intelligence Platform.

The Sprint 1 workflow includes:

1. Raw data inspection
2. Data cleaning and standardization
3. Data validation
4. SQLite database creation
5. ETL loading
6. Data-quality checks
7. Automated testing
8. Exploratory SQL analysis
9. Manual company-level QA
10. Final database integrity verification

---

# Dataset Coverage

The project uses **12 raw Excel source files**:

| Dataset          | Source File             |
| ---------------- | ----------------------- |
| Analysis         | `analysis.xlsx`         |
| Balance Sheet    | `balancesheet.xlsx`     |
| Cash Flow        | `cashflow.xlsx`         |
| Companies        | `companies.xlsx`        |
| Documents        | `documents.xlsx`        |
| Financial Ratios | `financial_ratios.xlsx` |
| Market Cap       | `market_cap.xlsx`       |
| Peer Groups      | `peer_groups.xlsx`      |
| Profit & Loss    | `profitandloss.xlsx`    |
| Pros & Cons      | `prosandcons.xlsx`      |
| Sectors          | `sectors.xlsx`          |
| Stock Prices     | `stock_prices.xlsx`     |

The raw files are cleaned and standardized before being loaded into the database.

---

# Database

The final SQLite database is:

```text
nifty100.db
```

The database contains the following tables:

```text
companies
sectors
profitandloss
balancesheet
cashflow
analysis
documents
prosandcons
stock_prices
financial_ratios
peer_groups
```

The database schema is defined in:

```text
db/schema.sql
```

SQLite foreign-key enforcement is enabled and was verified during final QA.

---

# Final Database Statistics

| Table            | Records |
| ---------------- | ------: |
| Companies        |      92 |
| Sectors          |      10 |
| Profit & Loss    |   1,073 |
| Balance Sheet    |   1,058 |
| Cash Flow        |   1,064 |
| Financial Ratios |   1,041 |
| Stock Prices     |   5,520 |
| Documents        |   1,456 |
| Pros & Cons      |      24 |
| Peer Groups      |     248 |
| Analysis         |       0 |

> `analysis` is currently a derived/placeholder table in the database schema and is not populated by the current Sprint 1 loader.

---

# ETL Pipeline

The ETL pipeline is organized under:

```text
src/etl/
```

Main components:

### `normaliser.py`

Responsible for standardizing fields such as:

* Years
* Tickers
* Text fields
* Numeric values
* Dates

### `validator.py`

Implements the Sprint 1 data-quality framework containing **DQ-01 through DQ-16**.

Validation areas include:

* Primary-key uniqueness
* Company/year uniqueness
* Foreign-key integrity
* Balance-sheet consistency
* Operating-margin checks
* Sales validation
* Net-cash validation
* Tax-rate validation
* Dividend validation
* URL validation
* EPS consistency
* Required fields
* Year coverage
* Null detection
* Duplicate detection

### `loader.py`

Loads the processed datasets into:

```text
nifty100.db
```

The loader also handles identifier normalization and relationships between source datasets.

---

# Data Quality Results

The master data validation report is stored at:

```text
data/reports/master_data_validation_report.json
```

The final DQ validation produced:

```text
Total failures: 7
Critical failures: 0
Warnings: 7
```

The validation results are stored at:

```text
output/validation_failures.csv
```

## Current warnings

The warnings include:

* One zero/negative sales record
* Three EPS sign-consistency warnings
* Limited P&L history for one company
* Limited Balance Sheet history
* Limited Cash Flow history
* Limited Financial Ratio history
* Null-related records associated with source data

These are documented as **warnings rather than critical failures**.

---

# Historical Coverage

The database was checked for companies with fewer than five years of financial history.

Result:

```text
Companies with fewer than 5 P&L years: 1

JIOFIN — Jio Financial Services Ltd
Available P&L years: 2
```

This is a documented historical-coverage limitation of the source data.

---

# TTM Records

The raw Profit & Loss dataset contains **TTM (Trailing Twelve Months)** records.

The source inspection identified:

```text
Raw TTM records: 100
Unique companies with TTM records: 99
```

TTM records are not treated as normal calendar/financial years. They are therefore not assigned artificial year values during standardization.

This prevents TTM data from being incorrectly represented as historical annual data.

---

# Automated Testing

Sprint 1 required automated ETL testing.

Final test result:

```text
35 passed in 0.18s
```

Therefore:

```text
35 / 35 tests passed
```

The test suite covers normalization and ETL-related functionality, including year and ticker normalization.

Run the test suite with:

```
```

---

# Environment setup (uv)

```bash
uv sync
```

Run everything through `uv run` so the pinned `.venv` is used:

```bash
uv run pytest -q
uv run python src/analytics/populate_ratios.py
```

---

# Sprint 3 — Screener Engine

Generic, config-driven stock screener over Sprint 2 output. One screening
observation per company (latest available `financial_ratios.year`, currently
2024 for all 92 companies), AND-combined metric filters, deterministic
ticker-ordered output. Read-only (SELECT only, never mutates the DB).

Engine: `src/screener/engine.py` · Config: `config/screener_config.yaml`

## Run

```bash
uv run pytest tests/screener -q          # 105 screener tests
uv run pytest -q                         # full suite (Sprint 2 + 3)
uv run python -c "from src.screener.engine import run_preset; print(run_preset('quality_compounder')['matched_count'])"
```

## Supported operators

`gt` (>), `gte` (>=), `lt` (<), `lte` (<=), `eq` (==), `neq` (!=).
Symbol aliases (`>`, `>=`, …) are also accepted in YAML.

## 15 metric mapping (config name → DB column)

| Config metric | Table | Column |
|---|---|---|
| `roe` | `financial_ratios` | `return_on_equity_pct` |
| `net_profit_margin` | `financial_ratios` | `net_profit_margin_pct` |
| `operating_profit_margin` | `financial_ratios` | `operating_profit_margin_pct` |
| `asset_turnover` | `financial_ratios` | `asset_turnover` |
| `debt_to_equity` | `financial_ratios` | `debt_to_equity` |
| `interest_coverage_ratio` | `financial_ratios` | `interest_coverage` |
| `total_debt` | `financial_ratios` | `total_debt_cr` |
| `pe_ratio` | `financial_ratios_source` | `pe_ratio` |
| `pb_ratio` | `financial_ratios_source` | `pb_ratio` |
| `dividend_yield` | `financial_ratios_source` | `dividend_yield` |
| `dividend_payout_ratio` | `financial_ratios` | `dividend_payout_ratio_pct` |
| `revenue_growth_5yr` | `financial_ratios` | `revenue_cagr_5yr` |
| `profit_growth_5yr` | `financial_ratios` | `pat_cagr_5yr` |
| `eps_growth_5yr` | `financial_ratios` | `eps_cagr_5yr` |
| `earnings_per_share` | `financial_ratios` | `earnings_per_share` |

Note: Sprint 2 computes ROCE in Python but persists no `roce` column, and
`financial_ratios_source.roce/current_ratio` are all-NULL — so no `roce`
filter is offered (documented, not silently invented).

## Missing-value behavior

`missing_value_policy: fail`. NULL/NaN/inf/-inf/non-numeric ⇒ the filter
FAILS for that company (NULL is never coerced to 0).

## D/E financial exception

`exceptions.debt_to_equity.excluded_sectors` (config-driven, case-insensitive;
includes `Financials` plus Banking/Financial Services/NBFC/Insurance for
robustness). Financial-sector rows WAIVE the D/E filter. Per-filter opt-out
via `apply_exception: false` — used by `debt_free_blue_chip`, where
debt-free must hold even for financials.

## ICR debt-free handling

Debt-free is detected via `total_debt_cr == 0` (NULL debt is never
debt-free), with `profitandloss.interest` as the interest signal:
interest missing ⇒ filter fails; interest == 0 ⇒ +inf (no division by zero,
passes positive thresholds); negative/invalid interest ⇒ +inf per
`negative_interest_policy`; debt 0 + interest > 0 ⇒ normal stored ICR.

## Six presets (all 5–50 on 2024 data)

| Preset | Count |
|---|---|
| `quality_compounder` (ROE≥15, NPM≥10, D/E≤1 exc-fin, rev5Y≥8) | 34 |
| `value_pick` (PE≤35, PB≤8, ROE≥12, D/E≤1.5 exc-fin) | 10 |
| `growth_accelerator` (rev≥12, PAT≥15, EPS≥12, ROE≥12) | 25 |
| `dividend_champion` (yield≥2, payout 20–150, ROE≥10, D/E≤1.5 exc-fin) | 19 |
| `debt_free_blue_chip` (D/E≤0.1 strict, ROE≥12, NPM≥8, ICR≥10) | 21 |
| `turnaround_watch` (rev≥8, PAT≥15, EPS≥12, ROE≥8) | 37 |

Counts are validated, never auto-relaxed or truncated:
`validate_result_count()` reports pass/fail per preset.

## Add a new preset

Add a block under `presets:` in `config/screener_config.yaml` using only
the metric/operator names above, then:

```bash
uv run python -c "from src.screener.engine import run_preset; print(run_preset('my_preset')['matched_count'])"
```

Debug a preset with per-filter attrition: `screen(preset_name=..., debug=True)`.

# Sprint 2 - Financial Ratio Engine

## Sprint Objective
Compute 50+ Key Performance Indicators (KPIs) for all 92 companies across all available years (2011-2024), handle formula edge cases (such as zero denominators and negative equity), and populate the `financial_ratios` table in SQLite for downstream analytics.

## How to Run Sprint 2

### 1. Run the Formula Unit Tests
To verify the ratio logic, CAGR edge cases, and cashflow KPI rules:
```bash
python -m pytest tests/kpi/test_formulas.py -v
```
**Expected Output:**
You should see all 26 tests pass successfully (`26 passed in ~0.10s`).

### 2. Run the Ratio Engine (ETL)
To compute the ratios and insert them into the database:
```bash
python src/analytics/populate_ratios.py
```
**Expected Output:**
The script runs silently but will generate two output files in the `output/` directory:
1. `output/capital_allocation.csv`: Contains the 8-pattern capital allocation labels for every company-year.
2. `output/ratio_edge_cases.log`: Contains logged anomalies where calculated ratios differ significantly from raw source data (categorized as Data Source Issues).

### 3. Verify the Database Output
To confirm the data was successfully loaded into SQLite, run:
```bash
python -c "import sqlite3; print('Total Rows:', sqlite3.connect('nifty100.db').execute('SELECT COUNT(*) FROM financial_ratios').fetchone()[0])"
```
**Expected Output:**
`Total Rows: 1288` (or any number >= 1,100).

### 4. Run the Screener Preview
To test the business query requirement (ROE > 15% and D/E < 1 for the year 2023):
```bash
python -c "import sqlite3; res = sqlite3.connect('nifty100.db').execute('SELECT COUNT(DISTINCT company_id) FROM financial_ratios WHERE return_on_equity_pct > 15 AND debt_to_equity < 1 AND year = 2023').fetchone()[0]; print(f'Companies passing screener: {res}')"
```
**Expected Output:**
`Companies passing screener: 29` (which satisfies the 15-50 target range).


# Sprint 3 - Composite Score & Peer Engine (Final)

## Sprint Objective
Finalize the financial screener by implementing a 0-100 composite quality score, grouping companies into 11 peer groups, computing percentile rankings, and generating final Excel reports and radar charts.

## How to Run the Final Sprint 3 Deliverables

### 1. Run the Screener & Composite Score Engine (Days 15-17)
```bash
python src/screener/engine.py
```
**What it does:**
- Computes the 0-100 composite quality score using P10/P90 sector-winsorized metrics.
- Updates the `financial_ratios` table with the `composite_quality_score`.
- Evaluates the 6 presets against the updated metrics.
- Generates `output/screener_output.xlsx` containing 6 sheets (one for each preset) with conditional formatting for threshold cells.

### 2. Run the Peer Analytics & Radar Charts (Days 18-20)
```bash
python src/analytics/peer.py
```
**What it does:**
- Loads the 11 logical peer groups (e.g. IT Services, Private Banks, FMCG).
- Computes `PERCENT_RANK` for 10 KPIs within each group (correctly inverting D/E).
- Populates the `peer_percentiles` table in `nifty100.db`.
- Safely logs `No peer group assigned` for unmapped companies.
- Exports 92 radar charts (one per company, comparing them to their peer average or Nifty 100 average) to `reports/radar_charts/`.
- Generates `output/peer_comparison.xlsx` containing 11 sheets, with median rows, gold-highlighted benchmark companies, and red/yellow/green color-coded percentiles.

### 3. Run the Test Suite (Day 21)
```bash
python -m pytest tests
```
**Expected Output:**
`131 passed in ~2.50s`. 
This proves all unit tests, screener logic, and data quality (DQ) checks pass flawlessly with 0 failures.


# Sprint 4 - Streamlit Dashboard & Valuation

## Sprint Objective
Build an interactive 8-screen financial dashboard using Streamlit to visualize company profiles, screeners, peer comparisons, trend analysis, sector distributions, capital allocation maps, and annual reports. Also includes a valuation module to compute FCF yields and overvaluation flags.

## How to Run the Dashboard

```bash
streamlit run src/dashboard/app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`.

## Dashboard Screens

1. **01 Home**: High-level market KPIs (Average ROE, Median P/E, Total Companies), an interactive Plotly donut chart breaking down sectors, and a leaderboard of the top 5 companies by composite quality score. Includes a year selector that updates all metrics dynamically.
2. **02 Profile**: Deep-dive into a single company via an autocomplete search bar. Displays key financial ratios as metric tiles, a 10-year bar chart for Revenue and Net Profit, a dual-axis line chart for ROE and ROCE, and automatically surfaces qualitative Pros & Cons badges.
3. **03 Screener**: Powerful interactive filtering tool mirroring the Sprint 3 core logic. Use 10 metric sliders or click one of the 6 pre-configured preset buttons (e.g. Quality Compounder, Debt-Free Blue Chip) to instantly filter the universe. Results update live and can be exported cleanly to CSV.
4. **04 Peers**: Select one of the 11 logical peer groups to view a comprehensive side-by-side KPI table with percentile-based color coding (green/yellow/red). Select any company to instantly visualize its performance against the peer group average using an 8-axis Plotly radar chart.
5. **05 Trends**: Multi-metric overlay analysis tool. Select up to 3 metrics for a company to view a 10-year historical line chart, complete with automatically calculated Year-over-Year (YoY) percentage change annotations overlaid on every single data point.
6. **06 Sectors**: View a comprehensive 3D Plotly bubble chart for any chosen sector where X = Revenue CAGR, Y = ROE, Bubble Size = Market Cap, and Color = Sub-industry. Below it sits a dynamic sector median KPI bar chart.
7. **07 Capital Allocation**: A visual hierarchy (Plotly Treemap) grouping all 92 companies by their 8 distinct capital allocation patterns (e.g., Cash Cow, Reinvestor). Clicking a pattern dynamically lists the constituent companies.
8. **08 Reports**: Central hub for downloading audited documents. Search for a company to access direct BSE PDF links for 10 years of Annual Reports. Broken/404 links automatically show a red "Report unavailable" badge.

## Valuation Module

Run the standalone valuation script to generate `valuation_summary.xlsx` and `valuation_flags.csv`:
```bash
python src/analytics/valuation.py
```
This module calculates Free Cash Flow (FCF) Yield, EV/EBITDA, 5-Year Median P/E, and compares the current P/E ratio to the sector median to automatically flag companies as **Caution** (Overvalued), **Discount** (Undervalued), or **Fair**.
