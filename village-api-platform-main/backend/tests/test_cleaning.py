import pandas as pd

from app.services.cleaning import (
    clean_codes,
    clean_dataframe,
    clean_text,
    extract_lookup_tables,
)


def test_clean_dataframe_normalises_text_and_codes():
    df = pd.DataFrame(
        {
            "stc": [" 23 ", "23", "asdf"],
            "state_name": [" madhya pradesh ", "MADHYA PRADESH", "MADHYA PRADESH"],
            "dtc": [1.0, "02", "x"],
            "district_name": [" bhopal ", "bhopal", "bhopal"],
            "sub_dt": [1, 2, "3"],
            "sub_district_name": ["  berasia ", "berasia", "berasia"],
            "plcn": ["60", "61", "62"],
            "village_name": [" babaiya ", "babaiya", "babaiya"],
        }
    )
    out = clean_dataframe(df)
    assert list(out["stc"]) == [23, 23, 0]
    assert list(out["dtc"]) == [1, 2, 0]
    assert list(out["plcn"]) == [60, 61, 62]
    assert out.loc[0, "state_name"] == "MADHYA PRADESH"
    assert out.loc[0, "district_name"] == "BHOPAL"
    assert out.loc[0, "sub_district_name"] == "BERASIA"
    assert out.loc[0, "village_name"] == "BABAIYA"


def test_codes_and_text_helpers_are_idempotent():
    df = pd.DataFrame(
        {
            "stc": [1, 1],
            "state_name": ["UTTAR PRADESH", "UTTAR PRADESH"],
            "dtc": [10, 10],
            "district_name": ["LUCKNOW", "LUCKNOW"],
            "sub_dt": [99, 99],
            "sub_district_name": ["TEHSIL A", "TEHSIL A"],
            "plcn": [1, 2],
            "village_name": ["VILL 1", "VILL 2"],
        }
    )
    once = clean_codes(clean_text(df))
    twice = clean_codes(clean_text(once))
    pd.testing.assert_frame_equal(once, twice)


def test_extract_lookup_tables_produces_normalised_sets():
    df = pd.DataFrame(
        {
            "stc": [1, 1, 1, 1, 1],
            "state_name": ["A", "A", "A", "A", "A"],
            "dtc": [10, 10, 10, 10, 20],
            "district_name": ["D1", "D1", "D1", "D1", "D2"],
            "sub_dt": [100, 100, 200, 200, 300],
            "sub_district_name": ["S1", "S1", "S2", "S2", "S3"],
            "plcn": [1, 2, 3, 4, 5],
            "village_name": ["V1", "V2", "V3", "V4", "V5"],
        }
    )
    tables = extract_lookup_tables(df)
    assert len(tables["states"]) == 1
    assert len(tables["districts"]) == 2
    assert len(tables["sub_districts"]) == 3
    assert len(tables["villages"]) == 5