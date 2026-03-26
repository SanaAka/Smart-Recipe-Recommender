"""Fix: add columns to recipes table for user-posted recipes."""
import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

load_dotenv(Path(__file__).parent / '.env')

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'recipe_recommender'),
    charset='utf8mb4',
)
cur = conn.cursor(dictionary=True)

def column_exists(table, column):
    cur.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (os.getenv('DB_NAME', 'recipe_recommender'), table, column)
    )
    return cur.fetchone() is not None

def index_exists(table, index_name):
    cur.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_NAME=%s",
        (os.getenv('DB_NAME', 'recipe_recommender'), table, index_name)
    )
    return cur.fetchone() is not None

# Add columns
for col, definition in [
    ('submitted_by', 'INT NULL DEFAULT NULL'),
    ('is_approved', 'TINYINT(1) DEFAULT 1'),
    ('created_at', 'TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP'),
]:
    if not column_exists('recipes', col):
        cur.execute(f"ALTER TABLE recipes ADD COLUMN {col} {definition}")
        conn.commit()
        print(f"  + Added column recipes.{col}")
    else:
        print(f"  = Column recipes.{col} already exists")

# Add index
if not index_exists('recipes', 'idx_recipes_submitted_by'):
    cur.execute("CREATE INDEX idx_recipes_submitted_by ON recipes(submitted_by)")
    conn.commit()
    print("  + Added index idx_recipes_submitted_by")
else:
    print("  = Index idx_recipes_submitted_by already exists")

cur.close()
conn.close()
print("\nDone!")
