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

# Get most common tags
print("Top 20 most common tags (these will work as cuisine searches):")
cursor.execute("""
    SELECT t.name, COUNT(*) as recipe_count
    FROM tags t
    JOIN recipe_tags rt ON t.id = rt.tag_id
    GROUP BY t.id
    ORDER BY recipe_count DESC
    LIMIT 20
""")

for row in cursor.fetchall():
    print(f"  - {row['name']}: {row['recipe_count']} recipes")

cursor.close()
conn.close()
