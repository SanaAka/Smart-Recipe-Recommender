import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv('backend/.env')

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor(dictionary=True)

# Check for Cambodian tag
cursor.execute("SELECT * FROM tags WHERE name LIKE '%Cambodian%'")
tags = cursor.fetchall()
print(f"Cambodian tags: {tags}")

# Check recipes with Cambodian tag
cursor.execute("""
    SELECT r.id, r.name 
    FROM recipes r
    JOIN recipe_tags rt ON r.id = rt.recipe_id
    JOIN tags t ON rt.tag_id = t.id
    WHERE t.name LIKE '%Cambodian%'
    LIMIT 5
""")
recipes = cursor.fetchall()
print(f"\nCambodian recipes: {recipes}")

# Check what cuisine tags exist
cursor.execute("""
    SELECT t.name, COUNT(rt.recipe_id) as recipe_count
    FROM tags t
    JOIN recipe_tags rt ON t.id = rt.tag_id
    GROUP BY t.name
    ORDER BY recipe_count DESC
    LIMIT 30
""")
cuisines = cursor.fetchall()
print(f"\nTop 30 tags by recipe count:")
for c in cuisines:
    print(f"  {c['name']}: {c['recipe_count']} recipes")

cursor.close()
conn.close()
