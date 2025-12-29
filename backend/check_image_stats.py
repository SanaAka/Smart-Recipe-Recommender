import mysql.connector, os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = cursor = conn.cursor(dictionary=True)

# Check what images we have
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT image_url) as unique_images
    FROM recipes 
    WHERE image_url IS NOT NULL AND image_url != ''
""")

stats = cursor.fetchone()
print(f"\nImage Statistics:")
print(f"  Total recipes with images: {stats['total']:,}")
print(f"  Unique image URLs: {stats['unique_images']:,}")

# Show most common image URLs
cursor.execute("""
    SELECT image_url, COUNT(*) as count 
    FROM recipes 
    WHERE image_url IS NOT NULL AND image_url != ''
    GROUP BY image_url 
    ORDER BY count DESC 
    LIMIT 5
""")

print(f"\nMost common image URLs:")
for row in cursor.fetchall():
    print(f"  {row['count']:,} recipes: {row['image_url'][:80]}")

conn.close()
