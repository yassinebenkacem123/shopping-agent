import sqlite3
import os
from pathlib import Path

DB_NAME = "store.db"
DB_PATH = Path("c:/Users/PC/Desktop/YASSINE/agentics AI/langchain/projects/shopping-agent") / DB_NAME

print("Fixing database at:", DB_PATH)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Drop existing orders table
cursor.execute("DROP TABLE IF EXISTS orders")

# Create orders table with correct schema
cursor.execute("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    total_price REAL NOT NULL,
    ordered_at TEXT DEFAULT (datetime('now'))
)
""")

conn.commit()

# Verify columns
cursor.execute("PRAGMA table_info(orders)")
cols = cursor.fetchall()
print("New orders schema:")
for col in cols:
    print(col)

conn.close()
print("Database fixed successfully.")
