from pathlib import Path
import pandas as pd

processed = Path("data/processed")

print("=" * 80)
print("PROCESSED DATASET INSPECTION")
print("=" * 80)

files = sorted(processed.glob("*.parquet"))

print(f"Parquet files: {len(files)}\n")

for file in files:
    try:
        df = pd.read_parquet(file)

        print("-" * 80)
        print(f"FILE: {file.name}")
        print(f"SHAPE: {df.shape}")
        print("COLUMNS:")
        for col in df.columns:
            print(f"  - {col}")

        print("SAMPLE:")
        print(df.head(2).to_string(index=False))

    except Exception as e:
        print(f"\nERROR reading {file.name}: {e}")

print("\n" + "=" * 80)
