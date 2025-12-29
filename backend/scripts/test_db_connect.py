"""
Simple script to test DB connection using .env values.
Run inside the backend virtualenv: `python scripts/test_db_connect.py`
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

import mysql.connector


def main():
    cfg = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', '')
    }

    print('Attempting to connect with:')
    print(f"Host: {cfg['host']}, Port: {cfg['port']}, User: {cfg['user']}, Database: {cfg['database']}")

    try:
        cnx = mysql.connector.connect(**cfg)
        print('Connected OK. Server version:', cnx.get_server_info())
        cnx.close()
        return 0
    except mysql.connector.Error as e:
        print('Connection failed:', e)
        # If localhost fails, suggest trying 127.0.0.1
        if cfg['host'] in ('localhost', '127.0.0.1'):
            alt = '127.0.0.1' if cfg['host'] == 'localhost' else 'localhost'
            print(f"Tip: try connecting with host='{alt}' to force TCP vs socket auth.")
        return 2

if __name__ == '__main__':
    sys.exit(main())
