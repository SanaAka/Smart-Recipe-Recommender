"""Test if app_v2.py can read .env correctly"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment exactly like app_v2.py does
env_path = Path(__file__).parent / '.env'
print(f"Loading .env from: {env_path}")
print(f".env exists: {env_path.exists()}")

load_dotenv(dotenv_path=env_path)

# Read credentials
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3306')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', 'recipe_recommender')

print("\nEnvironment variables loaded:")
print(f"DB_HOST={db_host}")
print(f"DB_PORT={db_port}")
print(f"DB_USER={db_user}")
print(f"DB_PASSWORD={'*' * len(db_password)} (length: {len(db_password)})")
print(f"DB_NAME={db_name}")

# Test MySQL connection
import mysql.connector

effective_host = '127.0.0.1' if db_host == 'localhost' else db_host

print(f"\nAttempting connection to {effective_host}...")
try:
    connection = mysql.connector.connect(
        host=effective_host,
        port=int(db_port),
        user=db_user,
        password=db_password,
        database=db_name
    )
    print("✓ SUCCESS! Database connection works with loaded .env")
    connection.close()
except mysql.connector.Error as err:
    print(f"✗ FAILED: {err}")
    print(f"\nActual password value: '{db_password}'")
    print(f"Password characters: {[c for c in db_password]}")
