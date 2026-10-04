"""Data cleaning pipeline for the Census 2011 village directory datasets.

Exposes small, composable, unit-testable cleaning functions used both by the
command-line seeder (`scripts/seed_data.py`, phase 1 ETL) and by analytic
workflows (phase 2) that need cleaned dataframes without re-seeding.
"""

from pathlib import Path

import pandas as pd

# The Madhya Pradesh workbook has a different, messy layout and is handled
# separately (state/district rows only; no sub-district or village rows).
MP_FILENAME = "Rdir_2011_23_MADHYA_PRADESH.xls"

# Canonical column order used by every cleaned dataframe.
CLEAN_COLUMNS = [
    "stc",
    "state_name",
    "dtc",
    "district_name",
    "sub_dt",
    "sub_district_name",
    "plcn",
    "village_name",
]

_CODE_COLUMNS = ["stc", "dtc", "sub_dt", "plcn"]
_TEXT_COLUMNS = [
    "state_name",
    "district_name",
    "sub_district_name",
    "village_name",
]


def read_sheet(filepath: Path) -> pd.DataFrame:
    """Read a Census 2011 worksheet into a raw dataframe."""
    if filepath.name == MP_FILENAME:
        df = pd.read_excel(filepath, header=None, dtype=str)
        df = df.iloc[:, [3, 4]]
        df.columns = ["dtc", "district_name"]
        df["stc"] = 23
        df["state_name"] = "MADHYA PRADESH"
        df["sub_dt"] = df["dtc"]
        df["sub_district_name"] = df["district_name"]
        df["plcn"] = 0
        df["village_name"] = ""
        return df

    df = pd.read_excel(filepath, header=0, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df.columns = CLEAN_COLUMNS
    return df


def clean_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce census codes to integers, dropping garbage values for village rows."""
    out = df.copy()
    for col in _CODE_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    return out


def clean_text(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise text fields: strip whitespace and collapse repeated spaces."""
    out = df.copy()
    for col in _TEXT_COLUMNS:
        out[col] = (
            out[col]
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.upper()
        )
    return out


def clean_dataframe(df: pd.DataFrame, filepath: Path | None = None) -> pd.DataFrame:
    """Run the full cleaning pipeline over a raw dataframe."""
    out = df
    if filepath is not None:
        out = read_sheet(filepath)
    out = clean_codes(out)
    out = clean_text(out)
    return out


def extract_lookup_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split a cleaned master dataframe into normalised lookup tables.

    Returns a dict with keys: states, districts, sub_districts, villages.
    Each table contains only the columns that survive normalisation.
    """
    states = (
        df[["stc", "state_name"]]
        .drop_duplicates(subset=["stc"])
        .sort_values("stc")
        .reset_index(drop=True)
    )
    districts = (
        df[df["dtc"] > 0][["stc", "dtc", "district_name"]]
        .drop_duplicates(subset=["stc", "dtc"])
        .reset_index(drop=True)
    )
    sub_districts = (
        df[df["sub_dt"] > 0][["stc", "dtc", "sub_dt", "sub_district_name"]]
        .drop_duplicates(subset=["dtc", "sub_dt"])
        .reset_index(drop=True)
    )
    villages = (
        df[df["plcn"] > 0][["stc", "dtc", "sub_dt", "plcn", "village_name"]]
        .drop_duplicates(subset=["sub_dt", "plcn"])
        .reset_index(drop=True)
    )
    return {
        "states": states,
        "districts": districts,
        "sub_districts": sub_districts,
        "villages": villages,
    }


def read_dataset_files(dataset_dir: Path) -> pd.DataFrame:
    """Read, clean, and concatenate every workbook under ``dataset_dir``."""
    files = sorted(dataset_dir.glob("*.xls")) + sorted(dataset_dir.glob("*.ods"))
    frames = [clean_dataframe(_read_file(fp), fp) for fp in files]
    return pd.concat(frames, ignore_index=True)


def _read_file(filepath: Path) -> pd.DataFrame:
    return read_sheet(filepath)