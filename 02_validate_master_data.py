from pathlib import Path
import pandas as pd
import json
from datetime import datetime

# ============================================================
# N100 FINANCIAL INTELLIGENCE
# PHASE 3 — MASTER DATA INTEGRITY VALIDATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "data" / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("N100 FINANCIAL INTELLIGENCE")
print("PHASE 3 — MASTER DATA INTEGRITY VALIDATION")
print("=" * 70)


# ============================================================
# FILE CONFIGURATION
# ============================================================

FILES = {
    "companies": "companies_clean.parquet",
    "sectors": "sectors_clean.parquet",
    "peer_groups": "peer_groups_clean.parquet",
    "analysis": "analysis_clean.parquet",
    "balance_sheet": "balance_sheet_clean.parquet",
    "cash_flow": "cash_flow_clean.parquet",
    "financial_ratios": "financial_ratios_clean.parquet",
    "market_cap": "market_cap_clean.parquet",
    "profit_loss": "profit_loss_clean.parquet",
    "pros_cons": "pros_cons_clean.parquet",
    "stock_prices": "stock_prices_clean.parquet",
    "documents": "documents_clean.parquet",
}


# ============================================================
# LOAD DATA
# ============================================================

data = {}

for name, filename in FILES.items():

    path = PROCESSED_DIR / filename

    if not path.exists():
        print(f"[ERROR] Missing file: {filename}")
        continue

    df = pd.read_parquet(path)

    data[name] = df

    print(f"[OK] {name:<20} {len(df):>8,} rows")


print()


# ============================================================
# VALIDATION REPORT STRUCTURE
# ============================================================

report = {
    "generated_at": datetime.now().isoformat(),
    "datasets": {},
    "company_coverage": {},
    "duplicate_analysis": {},
    "financial_integrity": {},
    "stock_price_integrity": {},
    "cross_dataset_integrity": {},
    "warnings": [],
}


# ============================================================
# DATASET SUMMARY
# ============================================================

print("-" * 70)
print("1. DATASET SUMMARY")
print("-" * 70)

for name, df in data.items():

    missing_cells = int(df.isna().sum().sum())

    duplicate_rows = int(df.duplicated().sum())

    report["datasets"][name] = {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
        "columns_list": df.columns.tolist(),
    }

    print(
        f"{name:<20} "
        f"rows={len(df):>7,} | "
        f"cols={len(df):>2} | "
        f"missing={missing_cells:>5,} | "
        f"duplicates={duplicate_rows:>5,}"
    )


# ============================================================
# COMPANY MASTER VALIDATION
# ============================================================

print()
print("-" * 70)
print("2. COMPANY MASTER VALIDATION")
print("-" * 70)

companies = data.get("companies")

if companies is not None:

    print("Columns:")
    print(companies.columns.tolist())

    # Detect company identifier
    possible_company_columns = [
        "company_id",
        "id",
        "company",
        "ticker",
        "symbol",
    ]

    company_col = None

    for col in possible_company_columns:
        if col in companies.columns:
            company_col = col
            break

    if company_col:

        company_ids = (
            companies[company_col]
            .dropna()
            .astype(str)
            .str.strip()
        )

        unique_companies = company_ids.nunique()

        print(f"Company identifier column : {company_col}")
        print(f"Total company records     : {len(companies):,}")
        print(f"Unique companies          : {unique_companies:,}")

        report["company_coverage"]["company_identifier_column"] = company_col
        report["company_coverage"]["total_company_records"] = len(companies)
        report["company_coverage"]["unique_companies"] = unique_companies

        if unique_companies != 92:
            warning = (
                f"Expected 92 companies but found "
                f"{unique_companies} unique companies."
            )

            print("[WARNING]", warning)
            report["warnings"].append(warning)

        duplicate_companies = (
            company_ids[
                company_ids.duplicated(keep=False)
            ]
            .unique()
            .tolist()
        )

        print(
            f"Duplicate company identifiers: "
            f"{len(duplicate_companies)}"
        )

        if duplicate_companies:
            print(duplicate_companies[:20])

        report["company_coverage"]["duplicate_company_ids"] = (
            duplicate_companies
        )

    else:

        print("[ERROR] Could not identify company identifier column.")

        report["warnings"].append(
            "Company identifier column could not be identified."
        )


# ============================================================
# COMPANY ID COVERAGE ACROSS DATASETS
# ============================================================

print()
print("-" * 70)
print("3. COMPANY COVERAGE ACROSS DATASETS")
print("-" * 70)

master_ids = set()

if companies is not None and company_col:

    master_ids = set(
        companies[company_col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    print(f"Master company count: {len(master_ids)}")


for name, df in data.items():

    if name == "companies":
        continue

    if "company_id" not in df.columns:
        print(f"{name:<20} -> no company_id column")
        continue

    ids = set(
        df["company_id"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    missing_from_master = sorted(ids - master_ids)

    missing_data = sorted(master_ids - ids)

    print(
        f"{name:<20} "
        f"companies={len(ids):>3} | "
        f"unknown={len(missing_from_master):>3} | "
        f"missing={len(missing_data):>3}"
    )

    report["company_coverage"][name] = {
        "unique_companies": len(ids),
        "unknown_company_ids": missing_from_master,
        "companies_without_records": missing_data,
    }


# ============================================================
# DUPLICATE KEY ANALYSIS
# ============================================================

print()
print("-" * 70)
print("4. DUPLICATE KEY ANALYSIS")
print("-" * 70)

duplicate_configs = {
    "balance_sheet": ["company_id", "year"],
    "cash_flow": ["company_id", "year"],
    "financial_ratios": ["company_id", "year"],
    "profit_loss": ["company_id", "year"],
    "market_cap": ["company_id", "year"],
    "documents": ["company_id", "year"],
    "stock_prices": ["company_id", "date"],
}

for name, keys in duplicate_configs.items():

    df = data.get(name)

    if df is None:
        continue

    missing_keys = [
        col for col in keys
        if col not in df.columns
    ]

    if missing_keys:
        print(
            f"{name:<20} -> missing columns: "
            f"{missing_keys}"
        )
        continue

    duplicate_mask = df.duplicated(
        subset=keys,
        keep=False
    )

    duplicate_count = int(duplicate_mask.sum())

    duplicate_groups = int(
        df.loc[duplicate_mask, keys]
        .drop_duplicates()
        .shape[0]
    )

    print(
        f"{name:<20} "
        f"duplicate rows={duplicate_count:>5,} | "
        f"duplicate groups={duplicate_groups:>5,}"
    )

    report["duplicate_analysis"][name] = {
        "keys": keys,
        "duplicate_rows": duplicate_count,
        "duplicate_groups": duplicate_groups,
    }

    # Save detailed duplicate records
    if duplicate_count > 0:

        duplicate_df = (
            df.loc[duplicate_mask]
            .sort_values(keys)
        )

        duplicate_path = (
            REPORT_DIR /
            f"{name}_duplicate_records.csv"
        )

        duplicate_df.to_csv(
            duplicate_path,
            index=False
        )

        print(
            f"   -> saved: "
            f"{duplicate_path.name}"
        )


# ============================================================
# FINANCIAL VALUE VALIDATION
# ============================================================

print()
print("-" * 70)
print("5. FINANCIAL VALUE VALIDATION")
print("-" * 70)


def check_negative_values(
    dataset_name,
    columns
):

    df = data.get(dataset_name)

    if df is None:
        return

    results = {}

    for col in columns:

        if col not in df.columns:
            continue

        numeric = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        negative_count = int(
            (numeric < 0).sum()
        )

        results[col] = negative_count

        if negative_count:
            print(
                f"{dataset_name:<20} "
                f"{col:<30} "
                f"negative={negative_count:,}"
            )

    report["financial_integrity"].setdefault(
        dataset_name,
        {}
    )

    report["financial_integrity"][
        dataset_name
    ]["negative_values"] = results


check_negative_values(
    "profit_loss",
    [
        "sales",
        "operating_profit",
        "profit_before_tax",
        "net_profit",
        "eps",
    ]
)

check_negative_values(
    "balance_sheet",
    [
        "equity_capital",
        "reserves",
        "total_liabilities",
        "fixed_assets",
        "total_assets",
    ]
)

check_negative_values(
    "market_cap",
    [
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
    ]
)


# ============================================================
# RATIO VALIDATION
# ============================================================

print()
print("-" * 70)
print("6. RATIO RANGE VALIDATION")
print("-" * 70)

ratios = data.get("financial_ratios")

if ratios is not None:

    ratio_ranges = {
        "net_profit_margin_pct": (-1000, 1000),
        "operating_profit_margin_pct": (-1000, 1000),
        "return_on_equity_pct": (-1000, 1000),
        "debt_to_equity": (-100, 100),
        "interest_coverage": (-1000, 10000),
        "asset_turnover": (-100, 1000),
        "dividend_payout_ratio_pct": (-1000, 1000),
    }

    ratio_report = {}

    for col, (low, high) in ratio_ranges.items():

        if col not in ratios.columns:
            continue

        values = pd.to_numeric(
            ratios[col],
            errors="coerce"
        )

        invalid = (
            (values < low) |
            (values > high)
        )

        count = int(invalid.sum())

        ratio_report[col] = {
            "lower_bound": low,
            "upper_bound": high,
            "invalid_count": count,
        }

        print(
            f"{col:<35} "
            f"invalid={count:,}"
        )

    report["financial_integrity"][
        "financial_ratios"
    ] = ratio_report


# ============================================================
# STOCK PRICE VALIDATION
# ============================================================

print()
print("-" * 70)
print("7. STOCK PRICE VALIDATION")
print("-" * 70)

stocks = data.get("stock_prices")

if stocks is not None:

    price_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "adjusted_close",
    ]

    stock_report = {}

    for col in price_columns:

        if col not in stocks.columns:
            continue

        values = pd.to_numeric(
            stocks[col],
            errors="coerce"
        )

        invalid = values <= 0

        count = int(invalid.sum())

        stock_report[col] = {
            "invalid_or_zero": count,
            "missing": int(values.isna().sum()),
        }

        print(
            f"{col:<20} "
            f"invalid={count:>5,} | "
            f"missing={int(values.isna().sum()):>5,}"
        )

    # OHLC logical validation
    if all(
        col in stocks.columns
        for col in [
            "open_price",
            "high_price",
            "low_price",
            "close_price",
        ]
    ):

        open_price = pd.to_numeric(
            stocks["open_price"],
            errors="coerce"
        )

        high_price = pd.to_numeric(
            stocks["high_price"],
            errors="coerce"
        )

        low_price = pd.to_numeric(
            stocks["low_price"],
            errors="coerce"
        )

        close_price = pd.to_numeric(
            stocks["close_price"],
            errors="coerce"
        )

        invalid_ohlc = (
            (high_price < open_price) |
            (high_price < close_price) |
            (high_price < low_price) |
            (low_price > open_price) |
            (low_price > close_price) |
            (low_price > high_price)
        )

        stock_report["invalid_ohlc_rows"] = int(
            invalid_ohlc.sum()
        )

        print(
            f"Invalid OHLC rows   : "
            f"{int(invalid_ohlc.sum()):,}"
        )

    report["stock_price_integrity"] = stock_report


# ============================================================
# BALANCE SHEET ACCOUNTING CHECK
# ============================================================

print()
print("-" * 70)
print("8. BALANCE SHEET ACCOUNTING CHECK")
print("-" * 70)

bs = data.get("balance_sheet")

if bs is not None:

    required = [
        "total_liabilities",
        "total_assets",
    ]

    if all(col in bs.columns for col in required):

        liabilities = pd.to_numeric(
            bs["total_liabilities"],
            errors="coerce"
        )

        assets = pd.to_numeric(
            bs["total_assets"],
            errors="coerce"
        )

        difference = (
            liabilities - assets
        ).abs()

        # Relative tolerance
        tolerance = (
            assets.abs() * 0.01 + 1
        )

        mismatch = (
            difference > tolerance
        )

        mismatch_count = int(
            mismatch.sum()
        )

        print(
            f"Balance sheet mismatches: "
            f"{mismatch_count:,}"
        )

        report["financial_integrity"][
            "balance_sheet"
        ] = {
            "accounting_mismatch_rows": mismatch_count
        }


# ============================================================
# P&L / CASH FLOW YEAR COVERAGE
# ============================================================

print()
print("-" * 70)
print("9. FINANCIAL HISTORY COVERAGE")
print("-" * 70)

history_datasets = [
    "profit_loss",
    "balance_sheet",
    "cash_flow",
    "financial_ratios",
    "market_cap",
]

for name in history_datasets:

    df = data.get(name)

    if df is None:
        continue

    if "company_id" not in df.columns:
        continue

    if "year" not in df.columns:
        continue

    years_per_company = (
        df.groupby("company_id")["year"]
        .nunique()
    )

    print(
        f"{name:<20} "
        f"min years={years_per_company.min():>3} | "
        f"median={years_per_company.median():>5.1f} | "
        f"max={years_per_company.max():>3}"
    )

    report["cross_dataset_integrity"][
        f"{name}_history"
    ] = {
        "minimum_years": int(
            years_per_company.min()
        ),
        "median_years": float(
            years_per_company.median()
        ),
        "maximum_years": int(
            years_per_company.max()
        ),
    }


# ============================================================
# CROSS-DATASET COMPANY-YEAR ALIGNMENT
# ============================================================

print()
print("-" * 70)
print("10. CROSS-DATASET ALIGNMENT")
print("-" * 70)

datasets_for_alignment = [
    "profit_loss",
    "balance_sheet",
    "cash_flow",
    "financial_ratios",
    "market_cap",
]

for name in datasets_for_alignment:

    df = data.get(name)

    if df is None:
        continue

    if not all(
        col in df.columns
        for col in ["company_id", "year"]
    ):
        continue

    keys = set(
        zip(
            df["company_id"].astype(str),
            df["year"].astype(str)
        )
    )

    report["cross_dataset_integrity"][
        f"{name}_company_year_keys"
    ] = len(keys)

    print(
        f"{name:<20} "
        f"company-year keys={len(keys):,}"
    )


# ============================================================
# SAMPLE DUPLICATES
# ============================================================

print()
print("-" * 70)
print("11. DUPLICATE SAMPLE")
print("-" * 70)

for name in [
    "balance_sheet",
    "financial_ratios",
    "profit_loss",
]:

    df = data.get(name)

    if df is None:
        continue

    if not all(
        col in df.columns
        for col in ["company_id", "year"]
    ):
        continue

    dup = df[
        df.duplicated(
            subset=["company_id", "year"],
            keep=False
        )
    ].sort_values(
        ["company_id", "year"]
    )

    if len(dup) == 0:
        print(f"{name:<20} no duplicates")
        continue

    print()
    print(f"{name.upper()} DUPLICATES:")

    print(
        dup.head(10).to_string(
            index=False
        )
    )


# ============================================================
# SAVE MASTER REPORT
# ============================================================

report_path = (
    REPORT_DIR /
    "master_data_validation_report.json"
)

with open(
    report_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report,
        f,
        indent=4,
        default=str
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)

print(
    f"Report saved to:\n"
    f"{report_path}"
)

print()
print("Generated duplicate reports:")
print(
    "data/reports/*_duplicate_records.csv"
)

print()
print("IMPORTANT:")
print(
    "Do NOT build the KPI engine until the duplicate "
    "financial-period issue is reviewed."
)

print("=" * 70)