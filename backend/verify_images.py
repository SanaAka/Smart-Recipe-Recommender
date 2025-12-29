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
cursor.execute('SELECT id, name, image_url FROM recipes WHERE id IN (1,2,3,4,5,100,200) ORDER BY id')

print("\n✓ Sample recipes with your custom images:\n")
for r in cursor.fetchall():
    print(f"ID {r['id']:3}: {r['name'][:50]:50}")
    print(f"       Image: {r['image_url']}")
    print()

conn.close()
