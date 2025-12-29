import mysql.connector, os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor(dictionary=True)

# Show sample of different recipes with their categorized images
cursor.execute("""
    SELECT id, name, image_url 
    FROM recipes 
    WHERE id IN (120, 225, 86, 157, 235, 47, 190)
    ORDER BY id
""")

print("\n✓ Sample recipes with varied images:\n")
for r in cursor.fetchall():
    print(f"{r['name'][:40]:40}")
    print(f"  → {r['image_url']}")
    print()

conn.close()
