"""
Fast bulk update - updates ALL remaining recipes with image URLs in one go
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def bulk_update_images():
    """Update all recipes with a default food image URL"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'recipe_recommender')
        )
        
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check count first
        cursor.execute("""
            SELECT COUNT(*) 
            FROM recipes 
            WHERE image_url IS NULL OR image_url = ''
        """)
        
        count = cursor.fetchone()[0]
        print(f"Found {count:,} recipes without image URLs")
        
        if count == 0:
            print("✓ All recipes already have image URLs!")
            return
        
        # Use a simple formula: generate image URL based on recipe ID
        # This is much faster than row-by-row updates
        print("Performing bulk update...")
        
        cursor.execute("""
            UPDATE recipes 
            SET image_url = CONCAT('https://source.unsplash.com/400x300/?food,recipe,', id)
            WHERE image_url IS NULL OR image_url = ''
        """)
        
        conn.commit()
        affected = cursor.rowcount
        
        print(f"\n✅ Successfully updated {affected:,} recipes!")
        print("\nAll recipes now have placeholder food images from Unsplash")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == '__main__':
    bulk_update_images()
