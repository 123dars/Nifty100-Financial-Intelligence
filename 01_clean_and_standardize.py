from pathlib import Path
import pandas as pd
import numpy as np
import re
import json
from datetime import datetime


# ============================================================
# N100 FINANCIAL INTELLIGENCE
# PHASE 2 — DATA CLEANING & STANDARDIZATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "data" / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FILE CONFIGURATION
# ============================================================

FILE_CONFIG = {
    "analysis": {
        "pattern": "*analysis.xlsx",
        "sheet": "Analysis",
        "header": 1,
        "output": "analysis_clean.csv",
    },

    "balance_sheet": {
        "pattern": "*balancesheet.xlsx",
        "sheet": "Balance Sheet",
        "header": 1,
        "output": "balance_sheet_clean.csv",
    },

    "cash_flow": {
        "pattern": "*cashflow.xlsx",
        "sheet": "Cash Flow",
        "header": 1,
        "output": "cash_flow_clean.csv",
    },

    "companies": {
        "pattern": "*companies.xlsx",
        "sheet": "Companies",
        "header": 1,
        "output": "companies_clean.csv",
    },

    "documents": {
        "pattern": "*documents.xlsx",
        "sheet": "Documents",
        "header": 1,
        "output": "documents_clean.csv",
    },

    "financial_ratios": {
        "pattern": "*financial_ratios.xlsx",
        "sheet": "Sheet1",
        "header": 0,
        "output": "financial_ratios_clean.csv",
    },

    "market_cap": {
        "pattern": "*market_cap.xlsx",
        "sheet": "Sheet1",
        "header": 0,
        "output": "market_cap_clean.csv",
    },

    "peer_groups": {
        "pattern": "*peer_groups.xlsx",
        "sheet": "Sheet1",
        "header": 0,
        "output": "peer_groups_clean.csv",
    },

    "profit_loss": {
        "pattern": "*profitandloss.xlsx",
        "sheet": "Profit & Loss",
        "header": 1,
        "output": "profit_loss_clean.csv",
    },

    "pros_cons": {
        "pattern": "*prosandcons.xlsx",
        "sheet": "Pros & Cons",
        "header": 1,
        "output": "pros_cons_clean.csv",
    },

    "sectors": {
        "pattern": "*sectors.xlsx",
        "sheet": "Sheet1",
        "header": 0,
        "output": "sectors_clean.csv",
    },

    "stock_prices": {
        "pattern": "*stock_prices.xlsx",
        "sheet": "Sheet1",
        "header": 0,
        "output": "stock_prices_clean.csv",
    },
}


# ============================================================
# COLUMN STANDARDIZATION
# ============================================================

COLUMN_ALIASES = {
    "id": "id",
    "company_id": "company_id",
    "company_name": "company_name",

    "year": "year",
    "date": "date",

    "sales": "sales",
    "expenses": "expenses",
    "operating_profit": "operating_profit",
    "opm_percentage": "operating_profit_margin_pct",
    "other_income": "other_income",
    "interest": "interest_expense",
    "depreciation": "depreciation",
    "profit_before_tax": "profit_before_tax",
    "tax_percentage": "tax_percentage",
    "net_profit": "net_profit",
    "eps": "earnings_per_share",
    "dividend_payout": "dividend_payout_ratio_pct",

    "equity_capital": "equity_capital",
    "reserves": "reserves",
    "borrowings": "borrowings",
    "other_liabilities": "other_liabilities",
    "total_liabilities": "total_liabilities",
    "fixed_assets": "fixed_assets",
    "cwip": "capital_work_in_progress",
    "investments": "investments",
    "other_asset": "other_assets",
    "total_assets": "total_assets",

    "operating_activity": "operating_cash_flow",
    "investing_activity": "investing_cash_flow",
    "financing_activity": "financing_cash_flow",
    "net_cash_flow": "net_cash_flow",

    "net_profit_margin_pct": "net_profit_margin_pct",
    "operating_profit_margin_pct": "operating_profit_margin_pct",
    "return_on_equity_pct": "return_on_equity_pct",
    "debt_to_equity": "debt_to_equity",
    "interest_coverage": "interest_coverage",
    "asset_turnover": "asset_turnover",
    "free_cash_flow_cr": "free_cash_flow_cr",
    "capex_cr": "capex_cr",
    "earnings_per_share": "earnings_per_share",
    "book_value_per_share": "book_value_per_share",
    "dividend_payout_ratio_pct": "dividend_payout_ratio_pct",
    "total_debt_cr": "total_debt_cr",
    "cash_from_operations_cr": "cash_from_operations_cr",

    "market_cap_crore": "market_cap_crore",
    "enterprise_value_crore": "enterprise_value_crore",
    "pe_ratio": "pe_ratio",
    "pb_ratio": "pb_ratio",
    "ev_ebitda": "ev_ebitda",
    "dividend_yield_pct": "dividend_yield_pct",

    "peer_group_name": "peer_group_name",
    "is_benchmark": "is_benchmark",

    "broad_sector": "broad_sector",
    "sub_sector": "sub_sector",
    "index_weight_pct": "index_weight_pct",
    "market_cap_category": "market_cap_category",

    "open_price": "open_price",
    "high_price": "high_price",
    "low_price": "low_price",
    "close_price": "close_price",
    "volume": "volume",
    "adjusted_close": "adjusted_close",

    "company_logo": "company_logo",
    "chart_link": "chart_link",
    "about_company": "about_company",
    "website": "website",
    "nse_profile": "nse_profile",
    "bse_profile": "bse_profile",
    "face_value": "face_value",
    "book_value": "book_value",
    "roce_percentage": "roce_percentage",
    "roe_percentage": "roe_percentage",

    "annual_report": "annual_report",
    "pros": "pros",
    "cons": "cons",

    "compounded_sales_growth": "compounded_sales_growth",
    "compounded_profit_growth": "compounded_profit_growth",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe",
}


# ============================================================
# HELPERS
# ============================================================

def normalize_column_name(column):
    """
    Convert messy Excel column names into snake_case.
    """

    if pd.isna(column):
        return "unknown_column"

    column = str(column).strip()

    # Remove weird unicode characters
    column = column.replace("—", "_")
    column = column.replace("–", "_")

    # Remove punctuation
    column = re.sub(r"[^A-Za-z0-9]+", "_", column)

    # Remove duplicate underscores
    column = re.sub(r"_+", "_", column)

    # Remove leading/trailing underscores
    column = column.strip("_")

    column = column.lower()

    return COLUMN_ALIASES.get(column, column)


def standardize_columns(df):
    """
    Standardize all column names.
    """

    df.columns = [
        normalize_column_name(col)
        for col in df.columns
    ]

    return df


def clean_string_columns(df):
    """
    Remove unnecessary whitespace from string columns.
    """

    for col in df.select_dtypes(include=["object"]).columns:

        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
            .replace({
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "NULL": pd.NA,
                "null": pd.NA,
                "N/A": pd.NA,
                "NA": pd.NA,
                "-": pd.NA,
            })
        )

    return df


def convert_numeric_columns(df):
    """
    Convert columns that are obviously numeric.
    """

    numeric_keywords = [
        "id",
        "capital",
        "reserve",
        "borrow",
        "liabil",
        "asset",
        "investment",
        "sales",
        "expense",
        "profit",
        "income",
        "interest",
        "depreciation",
        "tax",
        "eps",
        "cash",
        "flow",
        "margin",
        "equity",
        "coverage",
        "turnover",
        "free_cash",
        "capex",
        "debt",
        "market_cap",
        "enterprise_value",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "yield",
        "weight",
        "face_value",
        "book_value",
        "roce",
        "roe",
        "price",
        "volume",
    ]

    for col in df.columns:

        # Never convert these to numeric
        if col in [
            "company_id",
            "company_name",
            "year",
            "date",
            "website",
            "nse_profile",
            "bse_profile",
            "company_logo",
            "chart_link",
            "about_company",
            "annual_report",
            "pros",
            "cons",
            "peer_group_name",
            "broad_sector",
            "sub_sector",
            "market_cap_category",
            "compounded_sales_growth",
            "compounded_profit_growth",
            "stock_price_cagr",
        ]:
            continue

        if any(keyword in col for keyword in numeric_keywords):

            cleaned = (
                df[col]
                .astype("string")
                .str.replace(",", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )

            converted = pd.to_numeric(
                cleaned,
                errors="coerce"
            )

            # Only replace if conversion produced useful values
            if converted.notna().sum() > 0:
                df[col] = converted

    return df


def normalize_year_column(df):

    if "year" not in df.columns:
        return df

    def clean_year(value):

        if pd.isna(value):
            return pd.NA

        value = str(value).strip()

        # Examples:
        # Dec 2012
        # Mar-13
        # 2024
        # 2019

        match = re.search(r"(19|20)\d{2}", value)

        if match:
            return int(match.group())

        # Try pandas date conversion
        try:
            parsed = pd.to_datetime(
                value,
                errors="coerce"
            )

            if pd.notna(parsed):
                return int(parsed.year)

        except Exception:
            pass

        return pd.NA

    df["year"] = df["year"].apply(clean_year)

    return df


def normalize_date_column(df):

    if "date" not in df.columns:
        return df

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    return df


def remove_empty_rows(df):

    before = len(df)

    df = df.dropna(
        how="all"
    ).copy()

    removed = before - len(df)

    return df, removed


def remove_invalid_export_rows(df):

    """
    Protect against accidental repeated Excel title/header rows.
    """

    if "company_id" in df.columns:

        # Remove rows where company_id literally equals "company_id"
        df = df[
            df["company_id"]
            .astype("string")
            .str.lower()
            .ne("company_id")
        ]

    return df


def remove_duplicates(df):

    before = len(df)

    # Prefer natural keys where available
    if {"company_id", "year"}.issubset(df.columns):

        # For stock prices date is more appropriate
        if "date" in df.columns:

            subset = [
                "company_id",
                "date"
            ]

        else:

            subset = [
                "company_id",
                "year"
            ]

        df = df.drop_duplicates(
            subset=subset,
            keep="first"
        )

    else:

        df = df.drop_duplicates()

    removed = before - len(df)

    return df, removed


# ============================================================
# FIND FILE
# ============================================================

def find_source_file(pattern):

    matches = list(
        RAW_DIR.glob(pattern)
    )

    if not matches:
        return None

    # If multiple files exist, choose the newest
    matches.sort(
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    return matches[0]


# ============================================================
# PROCESS ONE FILE
# ============================================================

def process_file(dataset_name, config):

    print()
    print("=" * 70)
    print(f"PROCESSING: {dataset_name.upper()}")
    print("=" * 70)

    source_file = find_source_file(
        config["pattern"]
    )

    if source_file is None:

        print(
            f"WARNING: Source file not found: "
            f"{config['pattern']}"
        )

        return {
            "dataset": dataset_name,
            "status": "FILE_NOT_FOUND",
        }

    print(f"Source: {source_file.name}")

    # --------------------------------------------------------
    # READ EXCEL
    # --------------------------------------------------------

    try:

        df = pd.read_excel(
            source_file,
            sheet_name=config["sheet"],
            header=config["header"]
        )

    except Exception as e:

        print(f"ERROR reading file: {e}")

        return {
            "dataset": dataset_name,
            "status": "READ_ERROR",
            "error": str(e),
        }

    original_rows = len(df)
    original_columns = len(df.columns)

    print(
        f"Original shape: "
        f"{original_rows:,} rows × "
        f"{original_columns} columns"
    )

    # --------------------------------------------------------
    # STANDARDIZATION
    # --------------------------------------------------------

    df = standardize_columns(df)

    # --------------------------------------------------------
    # REMOVE EMPTY ROWS
    # --------------------------------------------------------

    df, empty_removed = remove_empty_rows(df)

    # --------------------------------------------------------
    # REMOVE EXPORT ARTIFACT ROWS
    # --------------------------------------------------------

    df = remove_invalid_export_rows(df)

    # --------------------------------------------------------
    # CLEAN STRINGS
    # --------------------------------------------------------

    df = clean_string_columns(df)

    # --------------------------------------------------------
    # NUMERIC CONVERSION
    # --------------------------------------------------------

    df = convert_numeric_columns(df)

    # --------------------------------------------------------
    # YEAR NORMALIZATION
    # --------------------------------------------------------

    df = normalize_year_column(df)

    # --------------------------------------------------------
    # DATE NORMALIZATION
    # --------------------------------------------------------

    df = normalize_date_column(df)

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    df, duplicate_removed = remove_duplicates(df)

    # --------------------------------------------------------
    # SORT DATA
    # --------------------------------------------------------

    sort_columns = []

    if "company_id" in df.columns:
        sort_columns.append("company_id")

    if "year" in df.columns:
        sort_columns.append("year")

    if "date" in df.columns:
        sort_columns.append("date")

    if sort_columns:

        df = df.sort_values(
            sort_columns,
            na_position="last"
        ).reset_index(drop=True)

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    output_csv = (
        PROCESSED_DIR /
        config["output"]
    )

    output_parquet = (
        PROCESSED_DIR /
        config["output"].replace(
            ".csv",
            ".parquet"
        )
    )

    df.to_csv(
        output_csv,
        index=False
    )

    # Parquet is useful for the later analytics pipeline
    try:

        df.to_parquet(
            output_parquet,
            index=False
        )

        parquet_status = "created"

    except Exception as e:

        parquet_status = f"failed: {e}"

    # --------------------------------------------------------
    # QUALITY METRICS
    # --------------------------------------------------------

    missing_cells = int(
        df.isna().sum().sum()
    )

    total_cells = (
        df.shape[0] *
        df.shape[1]
    )

    missing_percentage = (
        missing_cells /
        total_cells *
        100
        if total_cells > 0
        else 0
    )

    column_missing = {}

    for col in df.columns:

        missing_count = int(
            df[col].isna().sum()
        )

        if missing_count > 0:

            column_missing[col] = {
                "missing": missing_count,
                "percentage": round(
                    missing_count /
                    len(df) *
                    100,
                    2
                )
            }

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = {

        "dataset": dataset_name,

        "source_file": source_file.name,

        "processed_at": datetime.now().isoformat(),

        "status": "SUCCESS",

        "original_rows": original_rows,

        "final_rows": len(df),

        "original_columns": original_columns,

        "final_columns": len(df.columns),

        "empty_rows_removed": empty_removed,

        "duplicate_rows_removed": duplicate_removed,

        "missing_cells": missing_cells,

        "missing_percentage": round(
            missing_percentage,
            2
        ),

        "columns": list(df.columns),

        "missing_by_column": column_missing,

        "csv_output": str(output_csv),

        "parquet_output": str(output_parquet),

        "parquet_status": parquet_status,
    }

    report_file = (
        REPORT_DIR /
        f"{dataset_name}_quality.json"
    )

    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            indent=4,
            default=str
        )

    # --------------------------------------------------------
    # CONSOLE SUMMARY
    # --------------------------------------------------------

    print()
    print("SUCCESS")

    print(
        f"Final shape: "
        f"{len(df):,} rows × "
        f"{len(df.columns)} columns"
    )

    print(
        f"Empty rows removed: "
        f"{empty_removed:,}"
    )

    print(
        f"Duplicate rows removed: "
        f"{duplicate_removed:,}"
    )

    print(
        f"Missing cells: "
        f"{missing_cells:,} "
        f"({missing_percentage:.2f}%)"
    )

    print(
        f"CSV: {output_csv.name}"
    )

    print(
        f"Parquet: {parquet_status}"
    )

    return report


# ============================================================
# MASTER PIPELINE
# ============================================================

def main():

    print("=" * 70)
    print("N100 FINANCIAL INTELLIGENCE")
    print("PHASE 2 — DATA CLEANING & STANDARDIZATION")
    print("=" * 70)

    print()
    print(f"Raw directory:")
    print(RAW_DIR)

    print()
    print(f"Processed directory:")
    print(PROCESSED_DIR)

    print()
    print(f"Report directory:")
    print(REPORT_DIR)

    if not RAW_DIR.exists():

        print()
        print("ERROR: data/raw directory does not exist.")

        return

    reports = []

    # --------------------------------------------------------
    # PROCESS ALL DATASETS
    # --------------------------------------------------------

    for dataset_name, config in FILE_CONFIG.items():

        result = process_file(
            dataset_name,
            config
        )

        reports.append(result)

    # --------------------------------------------------------
    # MASTER REPORT
    # --------------------------------------------------------

    successful = sum(
        1
        for r in reports
        if r.get("status") == "SUCCESS"
    )

    failed = len(reports) - successful

    master_report = {

        "project": "N100 Financial Intelligence",

        "stage": "Phase 2 - Data Cleaning",

        "processed_at": datetime.now().isoformat(),

        "datasets_expected": len(
            FILE_CONFIG
        ),

        "datasets_successful": successful,

        "datasets_failed": failed,

        "datasets": reports,
    }

    master_report_file = (
        REPORT_DIR /
        "etl_master_report.json"
    )

    with open(
        master_report_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            master_report,
            f,
            indent=4,
            default=str
        )

    # --------------------------------------------------------
    # SUMMARY TABLE
    # --------------------------------------------------------

    print()
    print()
    print("=" * 70)
    print("ETL SUMMARY")
    print("=" * 70)

    print(
        f"{'DATASET':<22}"
        f"{'STATUS':<15}"
        f"{'ROWS':>10}"
        f"{'MISSING':>12}"
    )

    print("-" * 70)

    for report in reports:

        dataset = report.get(
            "dataset",
            "unknown"
        )

        status = report.get(
            "status",
            "UNKNOWN"
        )

        rows = report.get(
            "final_rows",
            "-"
        )

        missing = report.get(
            "missing_percentage",
            "-"
        )

        if isinstance(rows, int):

            rows_display = f"{rows:,}"

        else:

            rows_display = str(rows)

        if isinstance(missing, float):

            missing_display = (
                f"{missing:.2f}%"
            )

        else:

            missing_display = str(missing)

        print(
            f"{dataset:<22}"
            f"{status:<15}"
            f"{rows_display:>10}"
            f"{missing_display:>12}"
        )

    print("-" * 70)

    print(
        f"Successful datasets: "
        f"{successful}/{len(FILE_CONFIG)}"
    )

    print(
        f"Failed datasets: "
        f"{failed}"
    )

    print()
    print(
        f"Master report:"
    )

    print(
        master_report_file
    )

    print()
    print("=" * 70)
    print("PHASE 2 COMPLETE")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()