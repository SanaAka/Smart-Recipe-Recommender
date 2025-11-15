import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

password = os.getenv('DB_PASSWORD', '')
print(f"Testing connection with password: {password[:5]}..." if password else "No password found")

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password=password,
        database='recipe_recommender',
        use_pure=True,
        ssl_disabled=True
    )
    print("✓ Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recipes")
    count = cursor.fetchone()[0]
    print(f"✓ Recipes in database: {count:,}")
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {type(e).__name__}: {e}")
