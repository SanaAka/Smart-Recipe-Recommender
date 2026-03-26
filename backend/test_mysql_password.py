"""Quick test to find the correct MySQL password"""
import mysql.connector
import getpass

print("MySQL Connection Tester")
print("=" * 50)

host = input("Host (press Enter for 127.0.0.1): ").strip() or "127.0.0.1"
user = input("Username (press Enter for root): ").strip() or "root"
password = getpass.getpass("Password: ")

try:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password
    )
    print("\n✓ SUCCESS! Connection works!")
    print(f"\nYour settings:")
    print(f"DB_HOST={host}")
    print(f"DB_USER={user}")
    print(f"DB_PASSWORD={password}")
    
    # Check if database exists
    cursor = connection.cursor()
    cursor.execute("SHOW DATABASES LIKE 'recipe_recommender'")
    if cursor.fetchone():
        print("\n✓ Database 'recipe_recommender' exists")
    else:
        print("\n⚠ Database 'recipe_recommender' does NOT exist")
        print("You need to create it first")
    
    cursor.close()
    connection.close()
    
except mysql.connector.Error as err:
    print(f"\n✗ FAILED: {err}")
    print("\nTroubleshooting:")
    print("1. Check if MySQL is running (open MySQL Workbench)")
    print("2. Try the password you use in MySQL Workbench")
    print("3. If blank password, just press Enter when prompted")
