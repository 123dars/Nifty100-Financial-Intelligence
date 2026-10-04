from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")

print("=" * 70)
print("N100 SOURCE FILE INSPECTION")
print("=" * 70)

for file in sorted(RAW_DIR.glob("*.xlsx")):
    print(f"\n{'=' * 70}")
    print(f"FILE: {file.name}")
    print("=" * 70)

    try:
        sheets = pd.read_excel(file, sheet_name=None)

        for sheet_name, df in sheets.items():
            print(f"\nSHEET: {sheet_name}")
            print(f"Rows: {len(df)}")
            print(f"Columns: {len(df.columns)}")
            print("Columns:")

            for col in df.columns:
                print(f"  - {col}")

            print("\nFirst 2 rows:")
            print(df.head(2).to_string(index=False))

    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)
