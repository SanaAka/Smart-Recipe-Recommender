"""
Update existing recipes in database with image URLs
Uses Unsplash API to generate food images based on recipe names
"""

import mysql.connector
import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

def update_recipe_images():
    """Update existing recipes with image URLs"""
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'recipe_recommender')
        )
        
        cursor = conn.cursor(dictionary=True)
        
        print("Connected to database successfully")
        
        # Get all recipes without image URLs
        cursor.execute("""
            SELECT id, name 
            FROM recipes 
            WHERE image_url IS NULL OR image_url = ''
            LIMIT 10000
        """)
        
        recipes = cursor.fetchall()
        total = len(recipes)
        
        if total == 0:
            print("✓ All recipes already have image URLs!")
            return
        
        print(f"Found {total} recipes without image URLs")
        print("Updating recipes with food images...")
        
        update_cursor = conn.cursor()
        batch_size = 1000
        count = 0
        
        for recipe in recipes:
            # Generate image URL from Unsplash (random food images)
            # Format: https://source.unsplash.com/400x300/?food,recipe-keywords
            recipe_keywords = recipe['name'].replace(' ', ',').replace('&', 'and')
            image_url = f"https://source.unsplash.com/400x300/?food,{recipe_keywords}"
            
            # Update recipe
            update_cursor.execute("""
                UPDATE recipes 
                SET image_url = %s 
                WHERE id = %s
            """, (image_url, recipe['id']))
            
            count += 1
            
            # Commit in batches
            if count % batch_size == 0:
                conn.commit()
                print(f"  Updated {count}/{total} recipes...")
        
        # Final commit
        conn.commit()
        
        print(f"\n✅ Successfully updated {count} recipes with image URLs!")
        print("\nImage source: Unsplash (random food images)")
        print("Note: These are placeholder images. For production, consider:")
        print("  - Using a dataset with actual recipe photos")
        print("  - Storing your own recipe images")
        print("  - Using a food image API with better matching")
        
        update_cursor.close()
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Error updating recipes: {e}")
        raise

if __name__ == '__main__':
    update_recipe_images()
