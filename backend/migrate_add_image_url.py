"""
Migration script to add image_url and source_url columns to existing recipes table
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Add image_url and source_url columns to recipes table"""
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'recipe_recommender')
        )
        
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'recipes' 
            AND COLUMN_NAME = 'image_url'
        """, (os.getenv('DB_NAME', 'recipe_recommender'),))
        
        if cursor.fetchone()[0] > 0:
            print("Column 'image_url' already exists. Skipping migration.")
        else:
            # Add image_url column
            print("Adding image_url column to recipes table...")
            cursor.execute("""
                ALTER TABLE recipes 
                ADD COLUMN image_url VARCHAR(1000) AFTER description
            """)
            print("✓ Added image_url column")
        
        # Check if source_url exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'recipes' 
            AND COLUMN_NAME = 'source_url'
        """, (os.getenv('DB_NAME', 'recipe_recommender'),))
        
        if cursor.fetchone()[0] > 0:
            print("Column 'source_url' already exists. Skipping migration.")
        else:
            # Add source_url column
            print("Adding source_url column to recipes table...")
            cursor.execute("""
                ALTER TABLE recipes 
                ADD COLUMN source_url VARCHAR(1000) AFTER image_url
            """)
            print("✓ Added source_url column")
        
        # Commit changes
        conn.commit()
        
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Optionally update existing recipes with image URLs")
        print("2. Restart your backend server")
        print("3. New recipes imported will automatically have image URLs")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"❌ Error during migration: {e}")
        raise

if __name__ == '__main__':
    migrate()
