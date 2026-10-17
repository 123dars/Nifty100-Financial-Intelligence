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

---

# Sprint 3 - Screener & Peer Engine (Final)

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

## Sprint Objective
Finalize the financial screener by implementing a 0-100 composite quality score, grouping companies into 11 peer groups, computing percentile rankings, and generating final Excel reports and radar charts.

## How to Run the Final Sprint 3 Deliverables

### 1. Run the Screener & Composite Score Engine 
```bash
python src/screener/engine.py
```
**What it does:**
- Computes the 0-100 composite quality score using P10/P90 sector-winsorized metrics.
- Updates the `financial_ratios` table with the `composite_quality_score`.
- Evaluates the 6 presets against the updated metrics.
- Generates `output/screener_output.xlsx` containing 6 sheets (one for each preset) with conditional formatting for threshold cells.

### 2. Run the Peer Analytics & Radar Charts 
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

### 3. Run the Test Suite 
```bash
python -m pytest tests
```
**Expected Output:**
`131 passed in ~2.50s`. 
This proves all unit tests, screener logic, and data quality (DQ) checks pass flawlessly with 0 failures.

---

# Sprint 4 - Dashboard & Valuation

## Sprint Objective
Deploy a fully working 8-screen Streamlit dashboard running on localhost:8501. Generate an automated valuation module to compute FCF yields and overvaluation/discount labels for all 92 companies.

## How to Run Sprint 4 Deliverables

### 1. Run the Valuation Module 
```bash
python src/analytics/valuation.py
```
**What it does:**
- Computes FCF yield for all 92 companies (FCF / market_cap_crore * 100).
- Computes sector median P/E and applies overvaluation flags (Caution / Discount / Fair).
- Generates output/valuation_summary.xlsx with complete multiples.
- Generates output/valuation_flags.csv isolating only Caution and Discount flagged companies.

### 2. Launch the Streamlit Dashboard 
To boot up the 8-screen frontend:
```bash
streamlit run src/dashboard/app.py
```
**What it does:**
- **01_home**: Renders the executive dashboard with KPIs and sector breakdowns.
- **02_profile**: Deep-dive individual company profiles with dual-axis 10-year line charts and qualitative Pros & Cons tags.
- **03_screener**: Filters companies live using 10 custom sliders and 6 presets, exporting directly to CSV.
- **04_peers**: Radar charts rendering 8-axis peer benchmark comparisons using dynamically computed percentiles.
- **05_trends**: Custom multi-metric trend overlays with YoY annotations.
- **06_sectors**: Revenue vs ROE interactive bubble chart scaled by Market Cap.
- **07_capital**: Generates a Plotly Treemap visualizing historical capital allocation patterns.
- **08_reports**: Link directory resolving 404-validated BSE annual report URLs.

---

# Sprint 5 - Cash Flow Intelligence, Reports & NLP

## Sprint Objective
By the end of Sprint 5, the NLP module must auto-generate pros and cons for all 92 companies with confidence scores. The Cash Flow Intelligence module must classify every company by CFO quality, CapEx intensity, and capital allocation pattern. All 92 company tearsheet PDFs and 11 sector PDFs must be generated with no text overflow or layout errors.

## How to Run Sprint 5 Deliverables

### 1. Run the NLP Extractors & Generators
```bash
python src/nlp/parser.py
python src/nlp/pros_cons_generator.py
```
**What it does:**
- `parser.py` extracts historical CAGRs and ROE from raw text via Regex and outputs `output/analysis_parsed.csv`.
- `pros_cons_generator.py` applies 12 Pro rules and 12 Con rules to generate algorithmic text with confidence scores, outputting to `output/pros_cons_generated.csv`.

### 2. Run the Cash Flow Intelligence Module
```bash
python src/analytics/cashflow_kpis.py
```
**What it does:**
- Computes CFO Quality Score, CapEx Intensity, Distress Signals, and Deleveraging flags.
- Generates `output/cashflow_intelligence.xlsx` and tracks distressed companies in `output/distress_alerts.csv`.
- Generates a capital allocation pattern change report in `output/pattern_changes.csv`.

### 3. Generate Batch PDF Reports
```bash
python src/reports/tearsheet.py
python src/reports/sector_report.py
python src/reports/portfolio_summary.py
```
**What it does:**
- `tearsheet.py` uses ReportLab to batch-generate 90 two-page PDF tearsheets (skipping 2 companies with insufficient data) to `reports/tearsheets/`.
- `sector_report.py` generates 10 sector summary PDFs to `reports/sector/`.
- `portfolio_summary.py` compiles the top KPIs into a single alphabetically sorted `reports/portfolio/portfolio_summary.pdf`.

---

# Sprint 6 — Stock Clustering, REST API, QA & Sign-Off

**Target Story Points:** 89 SP  
**Epics:** Epics 10, 11 & 12 — Clustering + REST API + QA + Final Sign-Off  
**Final Status:** Complete & Signed Off (All 20 Acceptance Gates Verified)

---

## Sprint Goal

By the end of Sprint 6, all 16 FastAPI endpoints must be live and returning correct data. KMeans clustering must assign all 92 companies to one of 5 labelled archetypes. The full pytest suite must show 60+ tests with 0 failures. All 20 acceptance gates must be verified and the project signed off on Day 45.

---

## Team Division & Execution

### 1. Priya Singh (Data Science & Analytics)
* **Day 36 — KMeans Clustering:**
  * Implemented `src/analytics/clustering.py` and `scripts/run_clustering.py` using 10 validated financial features:
    `net_profit_margin_pct`, `operating_profit_margin_pct`, `return_on_equity_pct`, `debt_to_equity`, `interest_coverage`, `asset_turnover`, `revenue_cagr_5yr`, `pat_cagr_5yr`, `pe_ratio`, `dividend_yield`.
  * Preprocessing: `+/-inf` replaced with NaN, median imputation (`SimpleImputer`), and feature standardization via `StandardScaler`.
  * Generated diagnostic elbow curve across K = 1..10 inertias saved to `reports/elbow_plot.png`.
* **Day 37 — Cluster Profiling & Statistics:**
  * Assigned all 92 companies to 5 distinct labelled behavioral archetypes:
    * **Cluster 0:** Growth-Oriented + High-Leverage Companies (15 companies, 16.3%)
    * **Cluster 1:** Low-Leverage Companies (33 companies, 35.9%)
    * **Cluster 2:** High Profitability Companies (2 companies, 2.2% — TCS, INFY)
    * **Cluster 3:** High Profitability + Growth-Oriented Companies (1 company, 1.1%)
    * **Cluster 4:** Balanced Financial Profile Stalwarts (41 companies, 44.6%)
  * Generated Pearson correlation heatmap saved to `reports/correlation_heatmap.png`.
  * Detected 13 outlier observations (|z| > 3.0) exported to `output/outlier_report.csv`.
  * Exported company-to-cluster mappings to `output/cluster_labels.csv`.
* **Day 43 — Performance Testing:**
  * Executed concurrent load tests: 10 concurrent requests executed in **0.048s** (< 10s budget).
  * Resolved and verified network port availability on `:8000` (API) and `:8501` (Dashboard) via `scripts/check_ports.py`.
  * Applied 7 idempotent covering SQLite B-Tree indexes via `scripts/optimize_sqlite.py`.

### 2. Vinay Todkar (Backend API & Integration)
* **Day 38 — FastAPI Server Scaffold:**
  * Created `src/api/main.py` and `src/api/db.py` providing SQLite connection management with `check_same_thread=False` and dictionary row factory.
  * Added CORS middleware (`allow_origins=["*"]`) and custom request timing and logging middleware.
  * Configured `/health` and `/api/health` monitoring endpoints.
* **Day 39 — Company Data Endpoints:**
  * `GET /api/companies`: List all 92 companies with search (`?q=`) and sector (`?sector=`) filters.
  * `GET /api/companies/{ticker}/profile`: Deep corporate profile with latest ratios, cluster archetype, peer group, and pros & cons.
  * `GET /api/companies/{ticker}/pnl`: Multi-year Profit & Loss statement history.
  * `GET /api/companies/{ticker}/balance-sheet`: Multi-year Balance Sheet statement history.
  * `GET /api/companies/{ticker}/cashflow`: Multi-year Cash Flow statement history.
  * `GET /api/companies/{ticker}/ratios`: Multi-year calculated ratios and quality scores.
  * `GET /api/companies/{ticker}/tearsheet`: Streaming download of the 2-page PDF tearsheet.
* **Day 40 — Screener, Sector, Peer & Remaining Endpoints:**
  * `GET /api/screener/presets`: Metadata and filter rules for all 6 screener presets.
  * `GET /api/screener/presets/{name}`: Execute preset screener strategy (returns 5–50 passing stocks).
  * `POST /api/screener/run`: Run custom multi-metric screener queries.
  * `GET /api/sectors`: Summary listing of 10 sectors with average margins and ROE.
  * `GET /api/sectors/{sector_name}`: Detailed member companies and metrics for a sector.
  * `GET /api/peers/{ticker}`: Peer group member listings and 10 KPI percentile ranks for radar charts.
  * `GET /api/market-cap`: Companies ranked by market capitalization with valuation flags.
  * `GET /api/portfolio/stats`: Index-wide aggregate summary statistics and cluster distributions.
  * `GET /api/documents/{ticker}`: Directory of BSE annual reports and filing links.
  * `GET /api/clusters`: Summary metrics for the 5 KMeans archetypes.
  * `GET /api/clusters/{cluster_id}`: Member company roster for a given cluster.
  * Exported complete OpenAPI 3.1 specification to `docs/openapi.json`.

### 3. Darshan B (QA, Testing, Documentation & Sign-Off)
* **Day 41 — ETL & KPI Unit Tests (`tests/test_etl_kpi.py`):**
  * Built unit tests for `normalize_year()` covering integers, strings, fiscal year ranges ('2023-24'), 'FY24', 'Mar-24', and TTM exclusions.
  * Validated loader counts: 92 companies, 10 sectors, ≥ 1000 P&L/BS/CF/Ratio records.
  * Tested 20 ratio edge cases (zero denominator, negative equity, negative sales, zero interest, infinite ICR, FCF missing components, etc.).
  * Built automated tests for 14 Data Quality rules (DQ-01 to DQ-14) covering key uniqueness, FK integrity, and balance sheet sanity.
* **Day 42 — API Tests & Integration (`tests/test_api_endpoints.py`, `tests/test_integration_streamlit_api.py`):**
  * Automated 29 REST API endpoint tests validating HTTP 200 codes, 404 error handling, and payload structures.
  * Automated 6 Streamlit-to-API integration tests confirming data model compatibility.
  * Executed full test suite and generated self-contained HTML test report: **`reports/pytest_report.html` (239 tests passed, 0 failures)**.
* **Day 44 — Documentation:**
  * Generated **`docs/analyst_guide.pdf`** (12 pages) containing comprehensive technical architecture, data dictionary, ratio formulations, screener rules, and operator runbooks.
  * Applied Black / Ruff automated formatting across all project packages (`45 files reformatted`).
  * Updated `README.md` to document the complete Sprint 6 production release.
* **Day 45 — Final Sign-Off:**
  * Verified all 20 acceptance gates.
  * Generated and signed off **`docs/acceptance_checklist.pdf`**.

---

## Deliverables & Exit Criteria Verification

| Deliverable Artifact | Path | Verification Status |
|---|---|:---:|
| **Cluster Labels** | `output/cluster_labels.csv` | **92 Companies Classified** |
| **Outlier Report** | `output/outlier_report.csv` | **13 Outlier Records (|z| > 3.0)** |
| **Elbow Curve Plot** | `reports/elbow_plot.png` | **Generated (K = 1..10 Inertias)** |
| **Correlation Heatmap** | `reports/correlation_heatmap.png` | **Generated (10 Features)** |
| **FastAPI REST Server** | `src/api/` (16+ Endpoints) | **Verified (HTTP 200 on all endpoints)** |
| **OpenAPI Specification** | `docs/openapi.json` | **Exported (23 KB JSON Spec)** |
| **Automated Test Report** | `reports/pytest_report.html` | **239 Tests Passing, 0 Failures** |
| **Analyst Guide Manual** | `docs/analyst_guide.pdf` | **12 Pages (Meets 10+ Pages Req)** |
| **Acceptance Checklist** | `docs/acceptance_checklist.pdf` | **20/20 Acceptance Gates Signed Off** |

---

## How to Run Sprint 6 Deliverables

### 1. Run the KMeans Clustering Pipeline
```bash
python scripts/run_clustering.py
```
*Outputs: `output/cluster_labels.csv`, `output/outlier_report.csv`, `reports/elbow_plot.png`, `reports/correlation_heatmap.png`.*

### 2. Apply SQLite Query Optimization
```bash
python scripts/optimize_sqlite.py
```
*Ensures 7 covering B-Tree indexes are created without altering row counts.*

### 3. Check Port Conflicts
```bash
python scripts/check_ports.py
```
*Verifies ports 8000 (API) and 8501 (Dashboard) are available.*

### 4. Start the FastAPI REST Backend
```bash
python src/api/main.py
```
*Server launches on `http://0.0.0.0:8000`. Interactive Swagger UI is available at `http://localhost:8000/docs`.*

### 5. Launch the Streamlit Analytical Dashboard
```bash
streamlit run src/dashboard/app.py
```
*Access the multi-screen dashboard at `http://localhost:8501`, including the new 09 Cluster Analysis page.*

### 6. Run the Full Automated Test Suite & Generate HTML Report
```bash
python -m pytest --html=reports/pytest_report.html --self-contained-html
```
*Runs all 240 automated unit, API, screener, KPI, and performance tests.*

### 7. Generate PDF Documentation Deliverables
```bash
python scripts/generate_sprint6_docs.py
```
*Generates `docs/analyst_guide.pdf` (12 pages) and `docs/acceptance_checklist.pdf`.*

