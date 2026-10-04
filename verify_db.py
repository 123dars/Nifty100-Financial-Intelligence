import sqlite3

conn = sqlite3.connect("nifty100.db")
conn.execute("PRAGMA foreign_keys = ON")

print("=" * 60)
print("N100 DATABASE VERIFICATION")
print("=" * 60)

print("Foreign keys:", conn.execute("PRAGMA foreign_keys").fetchone()[0])

table_count = conn.execute("""
    SELECT COUNT(*)
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
""").fetchone()[0]

print("Application tables:", table_count)

fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
print("FK violations:", len(fk_errors))

print("\nTables:")
tables = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

for table in tables:
    print(" -", table[0])

conn.close()

print("=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
