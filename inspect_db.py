import sqlite3
import os
from pathlib import Path

DB_NAME = "store.db"
DB_PATH = Path("c:/Users/PC/Desktop/YASSINE/agentics AI/langchain/projects/shopping-agent") / DB_NAME

print("DB Path:", DB_PATH)
print("Exists:", DB_PATH.exists())

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

for table_name in [t[0] for t in tables]:
    print(f"\nSchema for table {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    for col in cursor.fetchall():
        print(col)
    
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Row count: {count}")
    
    if table_name == 'products':
        cursor.execute("SELECT DISTINCT category FROM products")
        categories = [r[0] for r in cursor.fetchall()]
        print("Categories:", categories)

conn.close()
