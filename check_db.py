import sqlite3

conn = sqlite3.connect("nifty100.db")

tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("\nDATABASE TABLES")
print("=" * 50)

for (table,) in tables:
    print(table)

print("\nROW COUNTS")
print("=" * 50)

for (table,) in tables:
    if not table.startswith("sqlite_"):
        count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        print(f"{table}: {count} rows")

conn.close()
