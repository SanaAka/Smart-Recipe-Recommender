import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'smart_recipe_db')
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

# Search for meat-related ingredients
print("Searching for 'meat' ingredients:")
cursor.execute("""
    SELECT DISTINCT i.name, COUNT(*) as recipe_count
    FROM ingredients i
    JOIN recipe_ingredients ri ON i.id = ri.ingredient_id
    WHERE i.name LIKE '%meat%'
    GROUP BY i.id
    ORDER BY recipe_count DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  - {row['name']}: {row['recipe_count']} recipes")

print("\nSearching for 'poultry' ingredients:")
cursor.execute("""
    SELECT DISTINCT i.name, COUNT(*) as recipe_count
    FROM ingredients i
    JOIN recipe_ingredients ri ON i.id = ri.ingredient_id
    WHERE i.name LIKE '%poultry%' OR i.name LIKE '%chicken%' OR i.name LIKE '%turkey%'
    GROUP BY i.id
    ORDER BY recipe_count DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  - {row['name']}: {row['recipe_count']} recipes")

print("\nTop 20 most common ingredients:")
cursor.execute("""
    SELECT i.name, COUNT(*) as recipe_count
    FROM ingredients i
    JOIN recipe_ingredients ri ON i.id = ri.ingredient_id
    GROUP BY i.id
    ORDER BY recipe_count DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f"  - {row['name']}: {row['recipe_count']} recipes")

cursor.close()
conn.close()
