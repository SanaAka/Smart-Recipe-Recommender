import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM recipes WHERE image_url IS NULL OR image_url = ''")
print(f"Remaining recipes without images: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM recipes WHERE image_url IS NOT NULL AND image_url != ''")
print(f"Recipes with images: {cursor.fetchone()[0]}")

conn.close()
