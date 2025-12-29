import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing MySQL connection...")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"Port: {os.getenv('DB_PORT')}")
print(f"User: {os.getenv('DB_USER')}")
print(f"Database: {os.getenv('DB_NAME')}")
print(f"Password: {'*' * len(os.getenv('DB_PASSWORD', ''))}")

try:
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    print("\n✓ Connection successful!")
    
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"✓ MySQL version: {version[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM recipes")
    count = cursor.fetchone()
    print(f"✓ Total recipes: {count[0]:,}")
    
    cursor.close()
    connection.close()
    
except mysql.connector.Error as e:
    print(f"\n✗ Connection failed!")
    print(f"Error: {e}")
    print(f"\nPossible solutions:")
    print("1. Verify MySQL is running")
    print("2. Check if password is correct")
    print("3. Try resetting MySQL root password")
    print("4. Check if user 'root'@'127.0.0.1' has proper privileges")
