<div align="center">

# 📈 N100 Financial Intelligence Platform
### *Enterprise Financial Data Engineering, Quantitative Screening, Machine Learning & Analytics for the Nifty 100 Universe*

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite3](https://img.shields.io/badge/SQLite-3.35+-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Pytest](https://img.shields.io/badge/Tests-239%20Passed%20%7C%200%20Failed-success?style=for-the-badge&logo=pytest&logoColor=white)](reports/pytest_report.html)
[![Acceptance Gates](https://img.shields.io/badge/Acceptance%20Gates-20%20%2F%2020%20Verified-brightgreen?style=for-the-badge&logo=checkmarx&logoColor=white)](docs/acceptance_checklist.pdf)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000?style=for-the-badge&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)

<br/>

[🔴 **Launch Live Streamlit Dashboard**](https://nifty100-financial-intelligence.streamlit.app/) •
[⚡ **Interactive Swagger API Docs**](http://localhost:8000/docs) •
[📑 **Analyst User Guide (PDF)**](docs/analyst_guide.pdf) •
[✅ **Acceptance Checklist (PDF)**](docs/acceptance_checklist.pdf) •
[👥 **Development Team**](#-development-team)

</div>

---

## 🌟 Executive Summary & Key Highlights

The **N100 Financial Intelligence Platform** is an end-to-end, institutional-grade financial data engineering and quantitative analytics suite built for the **Nifty 100 universe**. Spanning 6 comprehensive sprint cycles and 12 agile epics, the platform automates data extraction from 12 heterogeneous raw Excel files into a strictly validated SQLite database, powering 50+ financial KPIs, configurable stock screeners, peer radar benchmarking, unsupervised machine learning archetypes, batch PDF tearsheets, a 9-screen Streamlit analytical UI, and a high-performance FastAPI REST server.

### 📊 Platform Metrics at a Glance

| 🏢 Company Universe | 🧮 Financial Ratios | 🎯 Screener Strategies | 🤖 ML Archetypes |
|:---:|:---:|:---:|:---:|
| **92 Active Stocks**<br/>across 10 Nifty sectors | **50+ KPIs Computed**<br/>over 14 years (2011–2024) | **6 Production Presets**<br/>5–50 stocks per strategy | **5 KMeans Clusters**<br/>10 standardized features |

| ⚡ REST API Engine | 🧪 Automated Tests | 📑 Research Reports | 🛡️ Data Quality |
|:---:|:---:|:---:|:---:|
| **16+ Production Endpoints**<br/>0.048s concurrent latency | **239 Passed / 0 Failed**<br/>100% test pass rate | **90 Company Tearsheets**<br/>+ 10 Sector PDF briefs | **16 DQ Rules (DQ-01..16)**<br/>0 critical schema errors |

---

## 📑 Table of Contents

* [🗺️ End-to-End Architecture & Sprint Flow](#-end-to-end-architecture--sprint-flow)
* [⚡ Prerequisites & Environment Setup](#-prerequisites--environment-setup)
* [🧱 Sprint 1 — Data Foundation & Ingestion](#-sprint-1--data-foundation--ingestion)
* [🧮 Sprint 2 — Financial Ratio & KPI Engine](#-sprint-2--financial-ratio--kpi-engine)
* [🎯 Sprint 3 — Screener & Peer Benchmarking Engine](#-sprint-3--screener--peer-benchmarking-engine)
* [📊 Sprint 4 — Analytics Dashboard & Automated Valuation](#-sprint-4--analytics-dashboard--automated-valuation)
* [🧠 Sprint 5 — Cash Flow Intelligence, NLP & Automated PDF Reporting](#-sprint-5--cash-flow-intelligence-nlp--automated-pdf-reporting)
* [🚀 Sprint 6 — Stock Clustering, REST API, QA Suite & Final Sign-Off](#-sprint-6--stock-clustering-rest-api-qa-suite--final-sign-off)
* [📋 Unified End-to-End Execution Runbook](#-unified-end-to-end-execution-runbook)
* [📌 Project Deliverables Tracker (23 Deliverables)](#-project-deliverables-tracker-23-deliverables)
* [⚡ Quick Reference — Key Commands](#-quick-reference--key-commands)
* [📜 Important Project Rules](#-important-project-rules)
* [🛡️ Project Acceptance Gates Verification Matrix (20/20)](#-project-acceptance-gates-verification-matrix-2020)
* [📁 Repository Structure](#-repository-structure)
* [👥 Development Team](#-development-team)

---

## 🗺️ End-to-End Architecture & Sprint Flow

The platform was built incrementally across 6 two-week sprint cycles. Every sprint builds upon strictly validated upstream artifacts:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                N100 FINANCIAL INTELLIGENCE PLATFORM                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│ 🧱 SPRINT 1: DATA FOUNDATION & INGESTION                                                        │
│ 12 Raw Excels ➔ Normalizer ➔ 16 Data Quality Rules (DQ-01..16) ➔ nifty100.db (11 SQLite Tables) │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│ 🧮 SPRINT 2: FINANCIAL RATIO & KPI ENGINE                                                       │
│ 50+ Financial KPIs (2011-2024) ➔ Edge Case Handling ➔ 8 Capital Allocation Archetypes           │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│ 🎯 SPRINT 3: SCREENER & PEER BENCHMARKING ENGINE                                                │
│ Config-Driven Engine ➔ 6 Presets ➔ Composite Quality (0-100) ➔ 11 Peer Groups ➔ 92 Radar Charts │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│ 📊 SPRINT 4: ANALYTICS DASHBOARD & AUTOMATED VALUATION                                          │
│ 9-Screen Streamlit Dashboard (localhost:8501) ➔ FCF Yields ➔ Overvaluation/Discount Multiples   │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│ 🧠 SPRINT 5: CASH FLOW INTELLIGENCE, NLP & REPORTING                                            │
│ NLP Parser & 24 Rules ➔ CFO Quality Scoring ➔ Batch PDF Generation (90 Tearsheets + 10 Sectors) │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│ 🚀 SPRINT 6: MACHINE LEARNING, REST API, QA & FINAL SIGN-OFF                                    │
│ KMeans Clustering (5 Archetypes) ➔ FastAPI (16+ Endpoints) ➔ 239 Test QA Suite ➔ Final Sign-Off │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Prerequisites & Environment Setup

### 💻 System Requirements
* **Python:** 3.10, 3.11, or 3.12
* **Database:** SQLite 3.35+ (with native Foreign Keys and Window Function support)
* **Operating System:** Windows, macOS, or Linux

### 📦 Installation via `uv` (Recommended — 10x Faster)
```bash
# 1. Clone the repository
git clone https://github.com/123dars/Nifty100-Financial-Intelligence.git
cd Nifty100-Financial-Intelligence

# 2. Synchronize virtual environment with pinned dependencies
uv sync

# 3. Verify setup by running the test suite
uv run pytest -q
```

### 🐍 Standard Installation via `pip` & `venv`
```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2. Install all dependencies
pip install -r requirements.txt
```

---

## 🧱 Sprint 1 — Data Foundation & Ingestion

> **Core Objective:** Build an ACID-compliant relational database foundation in SQLite (`nifty100.db`), clean and standardize 12 heterogeneous raw Excel files, and enforce a 16-rule Data Quality framework.

### 📂 Dataset Coverage (12 Raw Workbooks)
The ingestion pipeline processes 12 raw data sources under `data/raw/`:

| Source Workbook | Records Loaded | Contents & Primary Entities |
|---|---:|---|
| 🏢 `companies.xlsx` | 92 | Master list of 92 companies, tickers, CIN, ISIN, and sector assignments |
| 🏷️ `sectors.xlsx` | 10 | 10 Nifty sector classifications and macroeconomic groupings |
| 📈 `profitandloss.xlsx` | 1,073 | Annual income statements (Sales, Expenses, OPM%, PAT, EPS) |
| ⚖️ `balancesheet.xlsx` | 1,058 | Annual asset/liability positions (Equity, Reserves, Borrowings, Total Assets) |
| 💵 `cashflow.xlsx` | 1,064 | Operating (CFO), Investing (CFI), and Financing (CFF) cash flows |
| 📐 `financial_ratios.xlsx` | 1,288 | Multi-year historical valuation, solvency, and profitability multiples |
| 📉 `stock_prices.xlsx` | 5,520 | 5-year historical prices (Open, High, Low, Close, Volume) |
| 📑 `documents.xlsx` | 1,456 | Verified corporate annual report links and regulatory filings |
| ⚖️ `prosandcons.xlsx` | 24 | Qualitative analyst observations, moat flags, and risk factors |
| 👥 `peer_groups.xlsx` | 248 | Sub-industry peer assignments and classification benchmarks |
| 📊 `peer_percentiles.xlsx` | 920 | Peer-group percentile distributions (Sprint 3) |
| 📝 `analysis.xlsx` | 0 | Schema placeholder for future qualitative commentary tables |

### 🛠️ ETL Pipeline Architecture (`src/etl/`)
* **`normaliser.py`**: Standardizes fiscal years (e.g., `'2023-24'`, `'FY24'`, `'Mar-24'`), cleans ticker strings, converts all currency values into uniform Crore units, and isolates Trailing Twelve Months (TTM) records without polluting annual timeseries.
* **`validator.py`**: Implements 16 strict Data Quality checks (**DQ-01 through DQ-16**):
  * **DQ-01 to DQ-04:** Primary key uniqueness, Foreign key referential integrity, Mandatory column presence.
  * **DQ-05 to DQ-08:** Balance sheet equation verification ($Assets = Liabilities$), positive sales checks, non-negative equity.
  * **DQ-09 to DQ-12:** Tax rate bounds ($0\% \le t \le 100\%$), EPS sign consistency ($PAT > 0 \iff EPS > 0$), dividend payout sanity.
  * **DQ-13 to DQ-16:** URL format validation, timeseries year gap detection, outlier identification.
* **`loader.py`**: Atomic, transaction-wrapped SQLite loader with foreign-key pragmas enabled.

### 🧪 Data Quality Audit Results
* **Critical Failures:** `0` (Zero critical errors across all tables)
* **Non-Critical Warnings:** `7` (Preserved in `output/validation_failures.csv` and `data/reports/master_data_validation_report.json`):
  * *JIOFIN:* Documented source limitation — 2 years of P&L available due to recent demerger.
  * *EPS Consistency:* 3 turnaround quarters where one-off items altered operating margin signs.
  * *Sales Outlier:* 1 negative sales record in legacy source line.

### 🚀 Execution Commands
```bash
# Run Sprint 1 ETL Unit Tests (35 tests)
python -m pytest tests/etl/ -v

# Run the complete Ingestion & Validation Pipeline
python src/etl/loader.py
```

---

## 🧮 Sprint 2 — Financial Ratio & KPI Engine

> **Core Objective:** Compute 50+ Key Performance Indicators for all 92 companies across 2011–2024, safeguard mathematical edge cases against zero denominators and negative equity, and classify company-years into 8 capital allocation archetypes.

### 📐 Calculated KPI Metric Suites
* **Profitability:** Return on Equity (ROE), Return on Capital Employed (ROCE), Operating Profit Margin (OPM%), Net Profit Margin (NPM%), Cash Flow Margin.
* **Solvency & Capital Structure:** Debt-to-Equity (D/E), Interest Coverage Ratio (ICR), Total Debt (₹ Cr), Net Debt (₹ Cr).
* **Asset Efficiency:** Asset Turnover, Fixed Asset Turnover, Working Capital Days, Inventory Days.
* **Growth CAGRs:** 3-Year & 5-Year Compound Annual Growth Rates for Revenue, Operating Profit, PAT, and EPS.
* **Cash Flow Dynamics:** Free Cash Flow ($FCF = CFO - CapEx$), FCF Yield, CFO-to-PAT Conversion Ratio.

### 🛡️ Mathematical Edge-Case Formulations
1. **Zero Denominator Protection:** Ratio calculations automatically return `NULL` when denominators equal zero, preventing `ZeroDivisionError`.
2. **Negative Equity Safeguard:** When Total Equity $\le 0$, ROE is rendered `NULL` to avoid false positives (negative net income divided by negative equity yielding a positive ROE).
3. **Debt-Free Interest Coverage:** When Total Debt $= 0$ and Interest $\le 0$, ICR is recorded as $+\infty$ (passes all minimum coverage screener filters).
4. **CAGR with Sign Inversion:** When initial values are negative or zero, the engine evaluates normalized linear annualized growth to prevent complex number evaluations.

### 🏛️ Capital Allocation Taxonomy (8 Patterns)
Every company-year is evaluated against cash generation and reinvestment criteria:
* **Aggressive Reinvestor:** High CapEx / CFO ratio ($> 70\%$) with positive FCF.
* **Balanced Compounder:** Moderate CapEx with steady dividends and growing retained earnings.
* **Dividend / Shareholder Yield:** High dividend payout ($> 50\%$) with mature, low CapEx requirements.
* **Deleveraging Stalwart:** Significant debt repayment ($CFF_{debt} < 0$) using operating cash flows.
* **Cash Accumulator:** Operating cash flows predominantly added to cash reserves and liquid investments.
* **Debt-Funded Growth:** High CapEx financed by net borrowings rather than operating cash flow.
* **Asset Sale / Restructuring:** Positive cash flow from divestments alongside restructuring.
* **Stressed / Distressed:** Negative CFO paired with negative or flat retained earnings.

### 🚀 Execution Commands
```bash
# Run formula edge-case unit tests (26 tests)
python -m pytest tests/kpi/test_formulas.py -v

# Execute Ratio Engine and populate financial_ratios table
python src/analytics/populate_ratios.py

# Verify record count in SQLite (1,288 rows loaded)
python -c "import sqlite3; print('Total Ratios Loaded:', sqlite3.connect('nifty100.db').execute('SELECT COUNT(*) FROM financial_ratios').fetchone()[0])"
```

---

## 🎯 Sprint 3 — Screener & Peer Benchmarking Engine

> **Core Objective:** Build a configuration-driven, read-only stock screening engine supporting boolean logic, a sector-winsorized 0–100 composite quality score, and an 11-industry peer benchmarking framework generating 92 radar chart visualizations.

### ⚙️ Screener Architecture (`config/screener_config.yaml`)
* **Strict Read-Only Execution:** Pure SQL `SELECT` operations; completely immutable against the database.
* **Supported Operators:** `gt` (>), `gte` (>=), `lt` (<), `lte` (<=), `eq` (==), `neq` (!=).
* **Missing Value Policy:** `missing_value_policy: fail`. Records with `NULL` or non-numeric metrics fail filter gates; `NULL` is never coerced to zero.
* **Financial Sector Exemption:** Config-driven waiver exempts Banking, NBFC, and Financial Services from the Debt-to-Equity (D/E) threshold, with explicit opt-out toggles for strict debt-free strategies.

### 🏆 6 Investment Strategy Presets (All Returning 5–50 Stocks)

| Preset Name | Filter Criteria | Qualified Companies |
|---|---|:---:|
| 💎 **`quality_compounder`** | ROE $\ge 15\%$, NPM $\ge 10\%$, D/E $\le 1.0$ (exc. fin), Rev 5Y CAGR $\ge 8\%$ | **34** |
| 🏷️ **`value_pick`** | P/E $\le 35$, P/B $\le 8$, ROE $\ge 12\%$, D/E $\le 1.5$ (exc. fin) | **10** |
| 🚀 **`growth_accelerator`** | Rev 5Y $\ge 12\%$, PAT 5Y $\ge 15\%$, EPS 5Y $\ge 12\%$, ROE $\ge 12\%$ | **25** |
| 💰 **`dividend_champion`** | Div Yield $\ge 2.0\%$, Payout $20\%\text{--}150\%$, ROE $\ge 10\%$, D/E $\le 1.5$ | **19** |
| 🛡️ **`debt_free_blue_chip`** | Strict D/E $\le 0.1$ (all sectors), ROE $\ge 12\%$, NPM $\ge 8\%$, ICR $\ge 10$ | **21** |
| 🔄 **`turnaround_watch`** | Rev 5Y $\ge 8\%$, PAT 5Y $\ge 15\%$, EPS 5Y $\ge 12\%$, ROE $\ge 8\%$ | **37** |

### 📊 Composite Quality Scoring (0–100) & Peer Percentiles
* **Sector Winsorization:** To prevent sector bias (e.g., IT vs. Steel), metrics are winsorized at the 10th and 90th percentiles ($P_{10}, P_{90}$) by sector.
* **Peer Group Analytics:** 11 sub-industry peer groups (IT Services, Private Banks, FMCG, Auto, Pharmaceuticals, Oil & Gas, Metals, Power, Capital Goods, Telecom, Chemicals).
* **Percentile Engine:** Computes `PERCENT_RANK` across 10 KPIs within each peer group, correctly inverting inverse metrics (Debt-to-Equity where lower is better).
* **Radar Charts:** Batch generates 92 high-resolution radar charts comparing each company to its peer median across 8 standardized axes, saved to `reports/radar_charts/`.

### 🚀 Execution Commands
```bash
# Run Screener unit and preset tests (105 tests)
python -m pytest tests/screener/ -v

# Run Screener Engine and export Excel reports
python src/screener/engine.py

# Run Peer Analytics engine and generate 92 radar charts
python src/analytics/peer.py
```

---

## 📊 Sprint 4 — Analytics Dashboard & Automated Valuation

> **Core Objective:** Launch a production 9-screen Streamlit analytical web application (`localhost:8501`) and implement an automated valuation multiples engine calculating Free Cash Flow yields and sector-relative valuation multiples.

### 🖥️ Streamlit Multi-Page UI Architecture (`src/dashboard/pages/`)
The application features 9 dedicated analytical screens:

```text
src/dashboard/pages/
├── 01_Dashboard_Home.py       # Executive overview, macro KPIs & index movers
├── 02_Company_Profile.py      # Dual-axis 10-year financials & dynamic Pros & Cons
├── 03_Financial_Screener.py   # Live interactive sliders, presets & CSV export
├── 04_Peer_Comparison.py      # Interactive 8-axis Plotly radar benchmark charts
├── 05_Trend_Analysis.py       # Multi-company timeseries overlay with YoY rates
├── 06_Sector_Analysis.py      # Cross-sector margin comparison & bubble charts
├── 07_Capital_Allocation.py   # 10-year Plotly Treemaps visualizing cash deployment
├── 08_Annual_Reports.py       # Corporate filings directory with verified BSE links
└── 09_Cluster_Analysis.py     # Interactive 2D/3D visual exploration of ML clusters
```

### 🏷️ Automated Valuation Multiples Engine
* **FCF Yield Formulation:** $\text{FCF Yield} = \frac{\text{Free Cash Flow}}{\text{Market Capitalization}} \times 100\%$.
* **Sector-Median P/E Benchmarking:** Computes dynamic sector median P/E multiples to evaluate relative pricing.
* **Valuation Categorization:** Flags companies as **Caution** (P/E $> 1.5 \times$ sector median or negative FCF), **Discount** (P/E $< 0.8 \times$ sector median and positive FCF), or **Fair**.
* **Deliverables:** `output/valuation_summary.xlsx` and `output/valuation_flags.csv`.

### 🚀 Execution Commands
```bash
# Run Valuation Multiples Engine
python src/analytics/valuation.py

# Launch the Streamlit Interactive Dashboard
streamlit run src/dashboard/app.py
```

---

## 🧠 Sprint 5 — Cash Flow Intelligence, NLP & Automated PDF Reporting

> **Core Objective:** Implement an algorithmic NLP rule engine to extract financial metrics and generate company Pros & Cons, build a Cash Flow Intelligence diagnostic suite, and batch-generate publication-grade PDF research tearsheets.

### 📝 Algorithmic NLP Pros/Cons Engine (`src/nlp/`)
* **Regex Financial Parser (`src/nlp/parser.py`):** Calibrated pattern-matching extracting historical CAGRs, ROE performance, and balance sheet commentary from unstructured annual report text into `output/analysis_parsed.csv`.
* **Algorithmic Pros & Cons Generator (`src/nlp/pros_cons_generator.py`):** Evaluates 12 quantitative Pro rules and 12 quantitative Con rules with calibrated confidence scores (e.g., 5-year ROE $> 20\%$, dividend yield $> 3\%$, interest coverage $< 1.5$, promoter holding changes).
* **Deliverable:** `output/pros_cons_generated.csv` covering all 92 companies.

### 💵 Cash Flow Intelligence Suite (`src/analytics/cashflow_kpis.py`)
* **CFO Quality Score:** Ratio of Operating Cash Flow to Operating Profit ($CFO / EBITDA$), flagging non-cash revenue accumulation.
* **CapEx Intensity:** Measures capital reinvestment rate relative to sales ($CapEx / Revenue$).
* **Distress Early Warning:** Detects deteriorating working capital cycles, consecutive negative FCF, and debt-fueled dividend distributions (`output/distress_alerts.csv`).
* **Pattern Change Tracker:** Identifies strategic capital allocation transitions over the trailing 3 years (`output/pattern_changes.csv`).

### 📑 Automated Batch PDF Generation (`src/reports/`)
Using ReportLab, the platform compiles clean, vector-rendered executive reports:
* **Company Tearsheets (`src/reports/tearsheet.py`):** Generates 90 two-page publication-ready company tearsheets in `reports/tearsheets/` (incorporating key metrics, historical charts, peer percentiles, and NLP pros/cons).
* **Sector Summary Reports (`src/reports/sector_report.py`):** 10 multi-page sector overview reports in `reports/sector/`.
* **Portfolio Index Summary (`src/reports/portfolio_summary.py`):** High-level Nifty 100 index tearsheet in `reports/portfolio/portfolio_summary.pdf`.

### 🚀 Execution Commands
```bash
# Run NLP Parser and Pros/Cons Generator
python src/nlp/parser.py
python src/nlp/pros_cons_generator.py

# Run Cash Flow Intelligence diagnostics
python src/analytics/cashflow_kpis.py

# Generate batch PDF tearsheets and sector summaries
python src/reports/tearsheet.py
python src/reports/sector_report.py
python src/reports/portfolio_summary.py
```

---

## 🚀 Sprint 6 — Stock Clustering, REST API, QA Suite & Final Sign-Off

> **Core Objective:** Complete Epics 10, 11, and 12 (89 Story Points). Perform KMeans clustering across 10 standardized financial features, launch a 16-endpoint FastAPI REST backend, automate a 239-test QA suite with zero failures, and achieve formal project sign-off across all 20 acceptance gates.

### 👥 Team Division & Execution Breakdown

#### 👩‍💻 1. Priya Singh — Data Science & Analytics
* **Day 36 — KMeans Clustering Pipeline:**
  * Implemented `src/analytics/clustering.py` and `scripts/run_clustering.py` using 10 standardized financial features:
    `net_profit_margin_pct`, `operating_profit_margin_pct`, `return_on_equity_pct`, `debt_to_equity`, `interest_coverage`, `asset_turnover`, `revenue_cagr_5yr`, `pat_cagr_5yr`, `pe_ratio`, `dividend_yield`.
  * Preprocessing: Handled $\pm\infty$ values, median imputation (`SimpleImputer`), and feature scaling (`StandardScaler`).
  * Generated diagnostic elbow curve across $K = 1 \dots 10$ inertias saved to `reports/elbow_plot.png`.
* **Day 37 — Cluster Profiling & Statistics:**
  * Grouped all 92 companies into 5 distinct behavioral archetypes:
    * **Cluster 0: Growth-Oriented + High-Leverage Companies** (15 companies, 16.3%)
    * **Cluster 1: Low-Leverage Companies** (33 companies, 35.9%)
    * **Cluster 2: High Profitability Companies** (2 companies, 2.2% — TCS, INFY)
    * **Cluster 3: High Profitability + Growth-Oriented Companies** (1 company, 1.1%)
    * **Cluster 4: Balanced Financial Profile Stalwarts** (41 companies, 44.6%)
  * Generated Pearson correlation heatmap saved to `reports/correlation_heatmap.png`.
  * Identified 13 outlier records ($|z| > 3.0$) exported to `output/outlier_report.csv`.
  * Exported cluster mappings to `output/cluster_labels.csv`.
* **Day 43 — Performance Testing & Optimization:**
  * Executed concurrent load tests: 10 concurrent requests executed in **0.048s** (< 10s budget).
  * Audited network port availability for `:8000` (API) and `:8501` (Dashboard) via `scripts/check_ports.py`.
  * Applied 7 idempotent covering SQLite B-Tree indexes via `scripts/optimize_sqlite.py`.

#### 👨‍💻 2. Vinay Todkar — Backend API & Integration
* **Day 38 — FastAPI Server Scaffold:**
  * Created `src/api/main.py` and `src/api/db.py` with multi-threaded SQLite connection management (`check_same_thread=False`) and dictionary row factory.
  * Added CORS middleware (`allow_origins=["*"]`) and custom request timing and logging middleware.
  * Configured `/health` and `/api/health` monitoring endpoints.
* **Day 39 — Company Financial Endpoints:**
  * `GET /api/companies`: List 92 companies with search (`?q=`) and sector (`?sector=`) filters.
  * `GET /api/companies/{ticker}/profile`: Corporate profile with latest ratios, cluster archetype, peer group, and pros & cons.
  * `GET /api/companies/{ticker}/pnl`: Multi-year Profit & Loss statement history.
  * `GET /api/companies/{ticker}/balance-sheet`: Multi-year Balance Sheet statement history.
  * `GET /api/companies/{ticker}/cashflow`: Multi-year Cash Flow statement history.
  * `GET /api/companies/{ticker}/ratios`: Multi-year calculated ratios and quality scores.
  * `GET /api/companies/{ticker}/tearsheet`: Streaming download of the 2-page PDF tearsheet.
* **Day 40 — Screener, Sector, Peer & Analytical Endpoints:**
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

#### 👨‍💼 3. Darshan B — QA, Testing, Documentation & Sign-Off
* **Day 41 — ETL & KPI Unit Tests (`tests/test_etl_kpi.py`):**
  * Automated unit tests for `normalize_year()` covering integers, fiscal strings ('2023-24'), 'FY24', 'Mar-24', and TTM exclusions.
  * Validated loader row counts: 92 companies, 10 sectors, $\ge 1,000$ records across statements.
  * Verified 20 ratio edge cases (zero denominator, negative equity, negative sales, zero interest, infinite ICR, FCF edge cases).
  * Tested 14 Data Quality rules (DQ-01 to DQ-14) covering key uniqueness, FK integrity, and balance sheet sanity.
* **Day 42 — API Tests & Full Suite Integration (`tests/test_api_endpoints.py`, `tests/test_integration_streamlit_api.py`):**
  * Built 29 REST API endpoint tests validating HTTP 200 responses, 404 error payloads, and schema structures.
  * Built 6 Streamlit-to-API integration tests confirming data consistency.
  * Executed full test suite and generated self-contained HTML test report: **`reports/pytest_report.html` (239 tests passed, 0 failures)**.
* **Day 44 — Documentation & Code Quality:**
  * Compiled 12-page **`docs/analyst_guide.pdf`** covering system architecture, data dictionaries, ratio formulas, screener rules, and operator runbooks.
  * Applied Black / Ruff automated formatting across all project packages (`45 files reformatted`).
  * Structured comprehensive `README.md` documenting the complete platform lifecycle.
* **Day 45 — Final Project Sign-Off:**
  * Verified all 20 acceptance gates.
  * Signed and exported official **`docs/acceptance_checklist.pdf`**.

---

### 📦 Sprint 6 Deliverables & Verification Matrix

| Deliverable Artifact | Path | Verification Status |
|---|---|:---:|
| 🏷️ **Cluster Labels** | `output/cluster_labels.csv` | **92 Companies Classified** |
| 🔍 **Outlier Report** | `output/outlier_report.csv` | **13 Outlier Records (|z| > 3.0)** |
| 📉 **Elbow Curve Plot** | `reports/elbow_plot.png` | **Generated (K = 1..10 Inertias)** |
| 🗺️ **Correlation Heatmap** | `reports/correlation_heatmap.png` | **Generated (10 Features)** |
| ⚡ **FastAPI REST Server** | `src/api/` (16+ Endpoints) | **Verified (HTTP 200 on all endpoints)** |
| 📖 **OpenAPI Specification** | `docs/openapi.json` | **Exported (23 KB JSON Spec)** |
| 🧪 **Automated Test Report** | `reports/pytest_report.html` | **239 Tests Passing, 0 Failures** |
| 📑 **Analyst Guide Manual** | `docs/analyst_guide.pdf` | **12 Pages (Meets 10+ Pages Requirement)** |
| ✅ **Acceptance Checklist** | `docs/acceptance_checklist.pdf` | **20/20 Acceptance Gates Signed Off** |

### 🚀 Execution Commands
```bash
# 1. Run KMeans Clustering pipeline
python scripts/run_clustering.py

# 2. Apply SQLite B-Tree query optimizations
python scripts/optimize_sqlite.py

# 3. Verify network ports (8000 and 8501)
python scripts/check_ports.py

# 4. Start the FastAPI REST Backend
python src/api/main.py
# (Interactive Swagger UI available at http://localhost:8000/docs)

# 5. Execute full automated test suite and generate HTML report
python -m pytest --html=reports/pytest_report.html --self-contained-html

# 6. Generate PDF Analyst Guide and signed Acceptance Checklist
python scripts/generate_sprint6_docs.py
```

---

## 📋 Unified End-to-End Execution Runbook

To execute the entire N100 Financial Intelligence pipeline sequentially from raw data to full production deployment:

```bash
# =============================================================================
# STAGE 1: SPRINT 1 — DATA INGESTION & VALIDATION
# =============================================================================
python src/etl/loader.py

# =============================================================================
# STAGE 2: SPRINT 2 — RATIO ENGINE & CAPITAL ALLOCATION
# =============================================================================
python src/analytics/populate_ratios.py

# =============================================================================
# STAGE 3: SPRINT 3 — SCREENER & PEER RADAR CHARTS
# =============================================================================
python src/screener/engine.py
python src/analytics/peer.py

# =============================================================================
# STAGE 4: SPRINT 4 — VALUATION MULTIPLES ENGINE
# =============================================================================
python src/analytics/valuation.py

# =============================================================================
# STAGE 5: SPRINT 5 — NLP & BATCH REPORT GENERATION
# =============================================================================
python src/nlp/parser.py
python src/nlp/pros_cons_generator.py
python src/analytics/cashflow_kpis.py
python src/reports/tearsheet.py
python src/reports/sector_report.py
python src/reports/portfolio_summary.py

# =============================================================================
# STAGE 6: SPRINT 6 — CLUSTERING, REST API & DOCUMENTATION
# =============================================================================
python scripts/run_clustering.py
python scripts/optimize_sqlite.py
python scripts/generate_sprint6_docs.py

# =============================================================================
# STAGE 7: QUALITY ASSURANCE & VERIFICATION
# =============================================================================
python -m pytest --html=reports/pytest_report.html --self-contained-html

# =============================================================================
# STAGE 8: LAUNCH PRODUCTION SERVERS
# =============================================================================
# Terminal 1: FastAPI REST Backend
python src/api/main.py

# Terminal 2: Streamlit Interactive Dashboard
streamlit run src/dashboard/app.py
```

---

## 📌 Project Deliverables Tracker (23 Deliverables)

All 23 mandatory project deliverables across Sprints 1 to 6 have been completed, verified, and audited for final Day 45 project sign-off:

| ID | Sprint | Deliverable Description | Physical Location | Status |
|:---:|:---:|---|---|:---:|
| **D-01** | Sprint 1 | Relational SQLite Database | `data/nifty100.db` (and `./nifty100.db`) | ✅ **Done** |
| **D-02** | Sprint 1 | Load Audit Log | `output/load_audit.csv` | ✅ **Done** |
| **D-03** | Sprint 1 | Validation Failures / Warnings Log | `output/validation_failures.csv` | ✅ **Done** |
| **D-04** | Sprint 1 | Exploratory SQL Analysis Queries | `notebooks/exploratory_queries.sql` | ✅ **Done** |
| **D-05** | Sprint 2 | Financial Ratios Table (50+ KPIs) | `data/nifty100.db → financial_ratios` | ✅ **Done** |
| **D-06** | Sprint 2 | Capital Allocation 8-Pattern Dataset | `output/capital_allocation.csv` | ✅ **Done** |
| **D-07** | Sprint 3 | Stock Screener Excel Export | `output/screener_output.xlsx` | ✅ **Done** |
| **D-08** | Sprint 3 | Screener Strategy Declarative Config | `config/screener_config.yaml` | ✅ **Done** |
| **D-09** | Sprint 3 | Peer Group Comparison Workbook | `output/peer_comparison.xlsx` | ✅ **Done** |
| **D-10** | Sprint 3 | 92 Company Peer Radar Plots | `reports/radar_charts/` | ✅ **Done** |
| **D-11** | Sprint 4 | Streamlit Dashboard (8 Screens + Cluster Analysis) | `src/dashboard/app.py` | ✅ **Done** |
| **D-12** | Sprint 4 | Valuation Multiples & Flags Summary | `output/valuation_summary.xlsx` | ✅ **Done** |
| **D-13** | Sprint 5 | Cash Flow Intelligence Workbook | `output/cashflow_intelligence.xlsx` | ✅ **Done** |
| **D-14** | Sprint 5 | Algorithmic Pros & Cons Dataset | `output/pros_cons_generated.csv` | ✅ **Done** |
| **D-15** | Sprint 5 | NLP Parsed Historical Metrics | `output/analysis_parsed.csv` | ✅ **Done** |
| **D-16** | Sprint 5 | Publication PDF Company Tearsheets | `reports/tearsheets/` (90 PDFs) | ✅ **Done** |
| **D-17** | Sprint 5 | Sector Summary PDF Research Briefs | `reports/sector/` (10 PDFs) | ✅ **Done** |
| **D-18** | Sprint 5 | Nifty 100 Portfolio Summary PDF | `reports/portfolio/portfolio_summary.pdf` | ✅ **Done** |
| **D-19** | Sprint 6 | KMeans Stock Clustering Archetypes | `output/cluster_labels.csv` | ✅ **Done** |
| **D-20** | Sprint 6 | FastAPI REST Backend (16+ Endpoints) | `src/api/main.py` | ✅ **Done** |
| **D-21** | Sprint 6 | Automated Test Report (239 Passed) | `reports/pytest_report.html` | ✅ **Done** |
| **D-22** | Sprint 6 | Comprehensive Analyst Guide (12 Pages) | `docs/analyst_guide.pdf` | ✅ **Done** |
| **D-23** | Sprint 6 | Formal Acceptance Gates Checklist | `docs/acceptance_checklist.pdf` | ✅ **Done** |

---

## ⚡ Quick Reference — Key Commands

The platform provides an automated `Makefile` with standard CLI commands:

| Command | Action Description | Target Output / Service |
|---|---|---|
| `make load` | Ingest and validate all raw Excel workbooks (Day 05) | `data/nifty100.db`, `output/load_audit.csv` |
| `make ratios` | Generate and populate the `financial_ratios` table | `nifty100.db → financial_ratios`, `output/capital_allocation.csv` |
| `make test` | Run full pytest suite with HTML report generation | `reports/pytest_report.html` (239 passed, 0 failures) |
| `make report` | Batch generate company tearsheets, sector PDFs & portfolio report | `reports/tearsheets/`, `reports/sector/`, `reports/portfolio/` |
| `make dashboard` | Launch the Streamlit Interactive Analytical Dashboard | `http://localhost:8501` |
| `make api` | Launch the FastAPI REST Backend server | `http://localhost:8000` (Swagger UI at `/docs`) |
| `make clean` | Remove `__pycache__`, `.pytest_cache`, and temporary `.pyc` files | Project caches cleaned (Database untouched) |

---

## 📜 Important Project Rules

All pipeline components, analytics scripts, and test suites strictly comply with the following 8 fundamental platform rules:

1. **Header Offset Specification:** Always use `pd.read_excel(path, header=1)` for all core Excel source files.
2. **Company Identifier Standardization:** Always normalize `company_id` (trim whitespace and convert to uppercase) prior to performing database joins.
3. **Monetary Unit Uniformity:** All monetary balances and timeseries are strictly denominated in **INR Crore** (₹ Cr).
4. **Financial Sector Exemption:** Always skip the `Financials` sector (Banking, NBFC, Insurance) when evaluating the Debt-to-Equity ($D/E$) screener filter.
5. **CAGR Base-Year Handling:** If a CAGR calculation encounters a negative base year, return `TURNAROUND` instead of computing an undefined or misleading rate.
6. **Zero-Interest Protection:** If Interest Expense equals zero ($Interest = 0$), display `Debt Free` instead of performing division by zero.
7. **Simulated Dataset Disclaimers:** Clearly label simulated datasets (`stock_prices`, `market_cap`) as **SIMULATED** in dashboards, visual plots, and reports.
8. **Pre-Commit Verification:** Run `make test` before every Git commit. **Zero test failures are mandatory** across the entire test suite.

---

## 🛡️ Project Acceptance Gates Verification Matrix (20/20)

All 20 formal acceptance gates defined for the platform have been systematically audited and verified with **0 failures**:

| Gate # | Verification Gate | Verification Standard | Audit Method / Evidence | Result |
|:---:|---|---|---|:---:|
| **Gate 01** | 🧱 SQLite Database Integrity | Schema valid, foreign keys active, 11+ tables | `PRAGMA foreign_keys / integrity_check` | ✅ **PASSED** |
| **Gate 02** | 🏢 Company Universe Coverage | Exactly 92 Nifty 100 companies active | `SELECT COUNT(*) FROM companies` | ✅ **PASSED** |
| **Gate 03** | 🏷️ Sector Coverage | All 10 Nifty sectors populated | `SELECT COUNT(DISTINCT sector) FROM sectors` | ✅ **PASSED** |
| **Gate 04** | ⚖️ Financial Statements Coverage | P&L $\ge 1000$, BS $\ge 1000$, CF $\ge 1000$ | Automated statement row count audit | ✅ **PASSED** |
| **Gate 05** | 🧮 KPI Ratio Computations | 50+ ratios calculated across 2011–2024 | `tests/kpi/test_formulas.py` (26 tests) | ✅ **PASSED** |
| **Gate 06** | 🎯 Screener Engine Presets | All 6 presets return between 5 and 50 stocks | `tests/screener/test_presets.py` | ✅ **PASSED** |
| **Gate 07** | 🛡️ D/E Exception Handling | Financials sector waived from D/E limit | `tests/screener/test_exceptions.py` | ✅ **PASSED** |
| **Gate 08** | 👥 Peer Percentile Engine | 11 peer groups with 10 KPI percentile ranks | `SELECT COUNT(*) FROM peer_percentiles` | ✅ **PASSED** |
| **Gate 09** | 📊 Radar Visualizations | Radar chart PNGs generated for all companies | Audit of `reports/radar_charts/` (92 PNGs) | ✅ **PASSED** |
| **Gate 10** | 🏷️ Valuation Analysis | FCF yield & sector-median discount flags | `output/valuation_summary.xlsx` | ✅ **PASSED** |
| **Gate 11** | 💵 Cash Flow Intelligence | CFO Quality Score & CapEx Classifications | `output/cashflow_intelligence.xlsx` | ✅ **PASSED** |
| **Gate 12** | 📝 NLP Text Parsing | CAGR text extraction via calibrated regex | `output/analysis_parsed.csv` | ✅ **PASSED** |
| **Gate 13** | ⚖️ Algorithmic Pros & Cons | 12 Pro & 12 Con rules for all 92 companies | `output/pros_cons_generated.csv` | ✅ **PASSED** |
| **Gate 14** | 📑 PDF Tearsheets Batch | 90 two-page publication-quality tearsheets | Audit of `reports/tearsheets/` (90 PDFs) | ✅ **PASSED** |
| **Gate 15** | 🤖 KMeans Stock Clustering | K=5 clusters assigned for all 92 companies | `output/cluster_labels.csv` (92 rows) | ✅ **PASSED** |
| **Gate 16** | 📉 Clustering Diagnostics | Elbow plot and correlation heatmap generated | `reports/elbow_plot.png`, `heatmap.png` | ✅ **PASSED** |
| **Gate 17** | ⚡ FastAPI Server Scaffold | Server active with CORS, logging, and /health | `src/api/main.py` healthcheck test | ✅ **PASSED** |
| **Gate 18** | 🌐 16+ REST API Endpoints | Company, screener, peer, sector endpoints active | `tests/test_api_endpoints.py` (29 tests) | ✅ **PASSED** |
| **Gate 19** | ⏱️ Performance & Concurrency | 10 concurrent API calls in $< 10$s (0.048s actual) | `tests/performance/test_api_load.py` | ✅ **PASSED** |
| **Gate 20** | 🧪 Full Automated Test Suite | Test suite passing with 0 failures | `reports/pytest_report.html` (239 tests pass) | ✅ **PASSED** |

---

## 📁 Repository Structure

```text
N100-Financial-Intelligence/
├── config/                          # Declarative system configurations
│   ├── screener_config.yaml         # Screener metric mappings & 6 presets
│   └── settings.yaml                # Global platform settings
├── data/                            # Raw and processed datasets
│   ├── raw/                         # 12 original source Excel files
│   └── reports/                     # Data validation JSON reports
├── db/                              # Database definitions
│   ├── schema.sql                   # Relational DDL schema (11 tables)
│   └── nifty100.db                  # Validated SQLite production database
├── docs/                            # Formal project documentation
│   ├── analyst_guide.pdf            # 12-page comprehensive Analyst User Guide
│   ├── acceptance_checklist.pdf     # Formally signed 20-gate checklist
│   └── openapi.json                 # OpenAPI 3.1 REST API specification
├── output/                          # Pipeline analytical CSV & Excel outputs
│   ├── cluster_labels.csv           # 5 KMeans archetype assignments
│   ├── outlier_report.csv           # Statistical outlier records (|z| > 3.0)
│   ├── screener_output.xlsx         # Screener preset export workbook
│   ├── peer_comparison.xlsx         # Peer benchmark percentile tables
│   ├── valuation_summary.xlsx       # Multiples and valuation flags
│   ├── cashflow_intelligence.xlsx   # CFO quality & CapEx scores
│   └── pros_cons_generated.csv      # NLP-generated corporate strengths/risks
├── reports/                         # Visual & PDF research reports
│   ├── elbow_plot.png               # KMeans cluster inertia diagnostics
│   ├── correlation_heatmap.png      # Feature Pearson correlation matrix
│   ├── pytest_report.html           # 239-test execution HTML report
│   ├── radar_charts/                # 92 company peer radar plots
│   ├── tearsheets/                  # 90 two-page corporate tearsheets
│   ├── sector/                      # 10 sector summary PDF tearsheets
│   └── portfolio/                   # Nifty 100 portfolio summary PDF
├── scripts/                         # Operational & maintenance utilities
│   ├── check_ports.py               # Port collision checker (:8000, :8501)
│   ├── optimize_sqlite.py           # B-Tree index optimization script
│   ├── run_clustering.py            # End-to-end KMeans execution script
│   └── generate_sprint6_docs.py     # PDF documentation compilation engine
├── src/                             # Core Python source packages
│   ├── analytics/                   # Ratio, peer, valuation, cashflow & clustering
│   ├── api/                         # FastAPI backend server, database & routers
│   ├── dashboard/                   # 9-page Streamlit analytical dashboard
│   ├── etl/                         # Ingestion normaliser, validator & loader
│   ├── nlp/                         # Regex parser & algorithmic pros/cons
│   └── reports/                     # ReportLab PDF tearsheet compilers
├── tests/                           # Complete automated pytest suite (239 tests)
│   ├── etl/                         # Sprint 1 ingestion & normalization tests
│   ├── kpi/                         # Sprint 2 ratio formula edge case tests
│   ├── screener/                    # Sprint 3 screener & exception tests
│   ├── performance/                 # Sprint 6 concurrency & load tests
│   ├── test_api_endpoints.py        # Sprint 6 REST API verification tests
│   ├── test_etl_kpi.py              # Sprint 6 comprehensive unit tests
│   └── test_integration_streamlit_api.py # Sprint 6 integration tests
├── pyproject.toml                   # Project metadata and dependencies
├── requirements.txt                 # Pinned pip requirements
└── README.md                        # Master platform documentation
```

---

## 👥 Development Team

This platform was architected, engineered, and verified by:

* **Priya Singh** — Data Science, Financial Machine Learning & Performance Optimization
* **Vinay Todkar** — Backend API Engineering, FastAPI Architecture & Integration
* **Darshan B** — QA Engineering, Full-Stack Integration, PDF Automation & Project Lead

---

<div align="center">
  <sub>Built with ❤️ for institutional financial analysis and data engineering.</sub><br/>
  <sub>© 2026 N100 Financial Intelligence Platform. All rights reserved.</sub>
</div>
