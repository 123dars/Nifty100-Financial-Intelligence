"""ETL script to seed Census 2011 data into PostgreSQL.

Usage:
    uv run python scripts/seed_data.py
"""

import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlunparse

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text

from app.services.cleaning import extract_lookup_tables, read_dataset_files

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

parsed = urlparse(DATABASE_URL)
query_params = parse_qs(parsed.query)
ssl_mode = query_params.pop("sslmode", ["require"])[0]
sync_url = urlunparse(parsed._replace(scheme="postgresql", query=""))

engine = create_engine(sync_url, echo=False, connect_args={"sslmode": ssl_mode})

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"


def seed():
    print("Ensuring tables exist...")
    from app.models import State
    State.metadata.create_all(engine)
    print("Tables ready.\n")

    big = read_dataset_files(DATASET_DIR)
    print(f"Total rows after cleaning: {len(big)}")

    tables = extract_lookup_tables(big)
    states_df = tables["states"]
    districts_df = tables["districts"]
    subs_df = tables["sub_districts"]
    villages_df = tables["villages"]

    print(f"  Unique states: {len(states_df)}")
    print(f"  Unique districts: {len(districts_df)}")
    print(f"  Unique sub-districts: {len(subs_df)}")
    print(f"  Unique villages: {len(villages_df)}")

    state_code_to_id = {}
    state_rows = [(int(r["stc"]), r["state_name"]) for _, r in states_df.iterrows()]

    print("\nInserting states...", flush=True)
    raw_conn = engine.raw_connection()
    try:
        cur = raw_conn.cursor()
        args_str = ",".join(cur.mogrify("(%s,%s)", r).decode() for r in state_rows)
        cur.execute(f"INSERT INTO states (code, name) VALUES {args_str} ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name RETURNING id, code")
        for row in cur.fetchall():
            state_code_to_id[row[1]] = row[0]
        raw_conn.commit()
        print(f"  {len(state_code_to_id)} states")

        print("Inserting districts...", flush=True)
        district_code_to_id = {}
        district_rows = [
            (int(r["dtc"]), r["district_name"], state_code_to_id[int(r["stc"])])
            for _, r in districts_df.iterrows()
            if int(r["stc"]) in state_code_to_id
        ]
        args_str = ",".join(cur.mogrify("(%s,%s,%s)", r).decode() for r in district_rows)
        cur.execute(f"INSERT INTO districts (code, name, state_id) VALUES {args_str} ON CONFLICT (code, state_id) DO UPDATE SET name = EXCLUDED.name RETURNING id, code, state_id")
        for row in cur.fetchall():
            district_code_to_id[(row[2], row[1])] = row[0]
        raw_conn.commit()
        print(f"  {len(district_code_to_id)} districts")

        print("Inserting sub-districts...", flush=True)
        sub_code_to_id = {}
        sub_rows = []
        for _, r in subs_df.iterrows():
            sid = state_code_to_id.get(int(r["stc"]))
            did = district_code_to_id.get((sid, int(r["dtc"]))) if sid else None
            if did:
                sub_rows.append((int(r["sub_dt"]), r["sub_district_name"], did))
        args_str = ",".join(cur.mogrify("(%s,%s,%s)", r).decode() for r in sub_rows)
        cur.execute(f"INSERT INTO sub_districts (code, name, district_id) VALUES {args_str} ON CONFLICT (code, district_id) DO UPDATE SET name = EXCLUDED.name RETURNING id, code, district_id")
        for row in cur.fetchall():
            sub_code_to_id[(row[2], row[1])] = row[0]
        raw_conn.commit()
        print(f"  {len(sub_code_to_id)} sub-districts")

        print("Inserting villages...", flush=True)
        village_rows = []
        for _, r in villages_df.iterrows():
            sid = state_code_to_id.get(int(r["stc"]))
            did = district_code_to_id.get((sid, int(r["dtc"]))) if sid else None
            sdid = sub_code_to_id.get((did, int(r["sub_dt"]))) if did else None
            if sdid:
                village_rows.append((int(r["plcn"]), r["village_name"], sdid))

        BATCH = 50000
        total = len(village_rows)
        for i in range(0, total, BATCH):
            batch = village_rows[i : i + BATCH]
            args_str = ",".join(cur.mogrify("(%s,%s,%s)", r).decode() for r in batch)
            cur.execute(f"INSERT INTO villages (code, name, sub_district_id) VALUES {args_str} ON CONFLICT (code, sub_district_id) DO UPDATE SET name = EXCLUDED.name")
            raw_conn.commit()
            print(f"    {min(i + BATCH, total)}/{total}", flush=True)
        print(f"  {total} villages")

    finally:
        raw_conn.close()

    print("\n--- Summary ---")
    with engine.connect() as conn:
        print(f"States:        {conn.execute(text('SELECT COUNT(*) FROM states')).scalar()}")
        print(f"Districts:     {conn.execute(text('SELECT COUNT(*) FROM districts')).scalar()}")
        print(f"Sub-districts: {conn.execute(text('SELECT COUNT(*) FROM sub_districts')).scalar()}")
        print(f"Villages:      {conn.execute(text('SELECT COUNT(*) FROM villages')).scalar()}")


if __name__ == "__main__":
    seed()