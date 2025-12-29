from pathlib import Path
from dotenv import load_dotenv
import os, sys, traceback

# Load backend .env
env_path = Path(__file__).parent / 'backend' / '.env'
if not env_path.exists():
    print(f"ERROR: .env not found at {env_path}")
    sys.exit(2)
load_dotenv(dotenv_path=env_path)

host = os.getenv('DB_HOST') or '127.0.0.1'
port = int(os.getenv('DB_PORT') or 3306)
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
db = os.getenv('DB_NAME')

print(f"Attempting MySQL connection to {host}:{port} as user '{user}' (db={db})")

try:
    import mysql.connector
    cnx = mysql.connector.connect(host=host, port=port, user=user, password=password, database=db)
    print("Connection successful!")
    cnx.close()
    sys.exit(0)
except Exception as e:
    print("Connection failed:")
    traceback.print_exc()
    sys.exit(3)
