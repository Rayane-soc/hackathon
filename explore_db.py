import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('.cache.sqlite')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(f"- {table[0]}")

    # Get table structure
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"  Columns: {[col[1] for col in columns]}")

    # Get sample data
    try:
        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
        rows = cursor.fetchall()
        print(f"  Sample data ({len(rows)} rows):")
        for row in rows:
            print(f"    {row}")
    except Exception as e:
        print(f"  Error reading data: {e}")

    print()

conn.close()
