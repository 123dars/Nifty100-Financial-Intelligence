"""Data normalisation utilities: years, tickers, text fields, and dates."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd


def normalize_year(value: Any) -> int | None:
    """Standardize raw year inputs into an integer calendar/fiscal year (e.g., 2024).

    Handles patterns such as:
    - 2024, '2024' -> 2024
    - 'FY24', 'FY2024' -> 2024
    - 'Mar-24', 'Mar 2024', 'Dec 2012' -> 2024, 2012
    - '2023-24' -> 2024
    - 'TTM', 'N/A', None -> None (TTM is treated separately)
    """
    if value is None or pd.isna(value):
        return None

    val = str(value).strip()
    if not val or val.upper() in ("TTM", "N/A", "NA", "-", "NONE", "NULL"):
        return None

    # Check two-year fiscal year range e.g. 2023-24, 2023/24, 23-24
    m_range = re.search(r"(?:19|20)?(\d{2})[-/](\d{2})\b", val)
    if m_range:
        yy = int(m_range.group(2))
        return 2000 + yy if yy < 50 else 1900 + yy

    # Try FY followed by 4-digit or 2-digit: FY2024, FY24
    m_fy = re.search(r"FY\s*(19\d{2}|20\d{2})\b", val, re.IGNORECASE)
    if m_fy:
        return int(m_fy.group(1))

    m_fy2 = re.search(r"FY\s*(\d{2})\b", val, re.IGNORECASE)
    if m_fy2:
        yy = int(m_fy2.group(1))
        return 2000 + yy if yy < 50 else 1900 + yy

    # Try 4-digit year 19xx or 20xx anywhere
    m = re.search(r"\b(19\d{2}|20\d{2})\b", val)
    if m:
        year = int(m.group(1))
        if 1950 <= year <= 2050:
            return year

    # Two-digit year prefix: FY24, Mar-24, '24
    m_two = re.search(r"(?:FY|Mar-?|Dec-?|Sep-?|Jun-?|')(\d{2})\b", val, re.IGNORECASE)
    if m_two:
        yy = int(m_two.group(1))
        return 2000 + yy if yy < 50 else 1900 + yy

    # Bare 2-digit number if between 10 and 35
    if val.isdigit() and len(val) == 2:
        yy = int(val)
        return 2000 + yy if yy < 50 else 1900 + yy

    return None


def normalize_ticker(value: Any) -> str | None:
    """Clean and standardize company ticker symbols."""
    if value is None or pd.isna(value):
        return None
    val = str(value).strip().upper()
    val = re.sub(r"\.NS$|\.BO$", "", val)
    return val if val else None
