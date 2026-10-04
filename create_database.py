import sqlite3
from pathlib import Path

DB_PATH = Path("nifty100.db")
SCHEMA_PATH = Path("db/schema.sql")

if DB_PATH.exists():
    DB_PATH.unlink()

connection = sqlite3.connect(DB_PATH)

try:
    connection.execute("PRAGMA foreign_keys = ON")

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.executescript(schema)

    connection.commit()

    print("=" * 60)
    print("N100 FINANCIAL INTELLIGENCE - DATABASE INITIALIZATION")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print("Foreign keys: ON")

    tables = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """).fetchall()

    print(f"Tables created: {len(tables)}")

    for table in tables:
        print(f"  - {table[0]}")

finally:
    connection.close()
