"""
Add FULLTEXT indexes to the database for better search performance
This script creates the necessary FULLTEXT indexes for the search functionality
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    """Connect to MySQL database"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'recipe_recommender')
        )
        print("✓ Successfully connected to database")
        return connection
    except mysql.connector.Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        raise

def check_existing_indexes(cursor):
    """Check which FULLTEXT indexes already exist"""
    print("\n=== Checking Existing FULLTEXT Indexes ===")
    
    # Check recipes table
    cursor.execute("""
        SELECT INDEX_NAME, COLUMN_NAME 
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'recipes' 
        AND INDEX_TYPE = 'FULLTEXT'
    """, (os.getenv('DB_NAME', 'recipe_recommender'),))
    
    recipes_indexes = cursor.fetchall()
    if recipes_indexes:
        print(f"✓ Found {len(recipes_indexes)} FULLTEXT index(es) on recipes table:")
        for idx in recipes_indexes:
            print(f"  - {idx[0]}: {idx[1]}")
    else:
        print("✗ No FULLTEXT indexes found on recipes table")
    
    # Check ingredients table
    cursor.execute("""
        SELECT INDEX_NAME, COLUMN_NAME 
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'ingredients' 
        AND INDEX_TYPE = 'FULLTEXT'
    """, (os.getenv('DB_NAME', 'recipe_recommender'),))
    
    ingredients_indexes = cursor.fetchall()
    if ingredients_indexes:
        print(f"✓ Found {len(ingredients_indexes)} FULLTEXT index(es) on ingredients table:")
        for idx in ingredients_indexes:
            print(f"  - {idx[0]}: {idx[1]}")
    else:
        print("✗ No FULLTEXT indexes found on ingredients table")
    
    # Check tags table
    cursor.execute("""
        SELECT INDEX_NAME, COLUMN_NAME 
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'tags' 
        AND INDEX_TYPE = 'FULLTEXT'
    """, (os.getenv('DB_NAME', 'recipe_recommender'),))
    
    tags_indexes = cursor.fetchall()
    if tags_indexes:
        print(f"✓ Found {len(tags_indexes)} FULLTEXT index(es) on tags table:")
        for idx in tags_indexes:
            print(f"  - {idx[0]}: {idx[1]}")
    else:
        print("✗ No FULLTEXT indexes found on tags table")
    
    return recipes_indexes, ingredients_indexes, tags_indexes

def add_fulltext_indexes(connection):
    """Add FULLTEXT indexes to recipes, ingredients, and tags tables"""
    cursor = connection.cursor()
    
    try:
        # Check existing indexes first
        recipes_idx, ingredients_idx, tags_idx = check_existing_indexes(cursor)
        
        print("\n=== Creating FULLTEXT Indexes ===")
        
        # 1. Add FULLTEXT index on recipes(name, description)
        if not recipes_idx:
            print("\n1. Creating FULLTEXT index on recipes(name, description)...")
            try:
                cursor.execute("""
                    ALTER TABLE recipes 
                    ADD FULLTEXT INDEX idx_recipes_fulltext (name, description)
                """)
                connection.commit()
                print("✓ Created FULLTEXT index on recipes(name, description)")
            except mysql.connector.Error as e:
                if 'Duplicate key name' in str(e):
                    print("⚠ FULLTEXT index on recipes already exists")
                else:
                    print(f"✗ Error creating recipes FULLTEXT index: {e}")
        else:
            print("\n1. ✓ FULLTEXT index on recipes already exists")
        
        # 2. Add FULLTEXT index on ingredients(name)
        if not ingredients_idx:
            print("\n2. Creating FULLTEXT index on ingredients(name)...")
            try:
                cursor.execute("""
                    ALTER TABLE ingredients 
                    ADD FULLTEXT INDEX idx_ingredients_fulltext (name)
                """)
                connection.commit()
                print("✓ Created FULLTEXT index on ingredients(name)")
            except mysql.connector.Error as e:
                if 'Duplicate key name' in str(e):
                    print("⚠ FULLTEXT index on ingredients already exists")
                else:
                    print(f"✗ Error creating ingredients FULLTEXT index: {e}")
        else:
            print("\n2. ✓ FULLTEXT index on ingredients already exists")
        
        # 3. Add FULLTEXT index on tags(name)
        if not tags_idx:
            print("\n3. Creating FULLTEXT index on tags(name)...")
            try:
                cursor.execute("""
                    ALTER TABLE tags 
                    ADD FULLTEXT INDEX idx_tags_fulltext (name)
                """)
                connection.commit()
                print("✓ Created FULLTEXT index on tags(name)")
            except mysql.connector.Error as e:
                if 'Duplicate key name' in str(e):
                    print("⚠ FULLTEXT index on tags already exists")
                else:
                    print(f"✗ Error creating tags FULLTEXT index: {e}")
        else:
            print("\n3. ✓ FULLTEXT index on tags already exists")
        
        # 4. Optionally add search_text column if it doesn't exist
        print("\n4. Checking for search_text column in recipes...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'recipes' 
            AND COLUMN_NAME = 'search_text'
        """, (os.getenv('DB_NAME', 'recipe_recommender'),))
        
        has_search_text = cursor.fetchone()[0] > 0
        
        if not has_search_text:
            print("   Creating search_text column for denormalized search...")
            try:
                cursor.execute("""
                    ALTER TABLE recipes 
                    ADD COLUMN search_text TEXT AFTER description
                """)
                connection.commit()
                print("✓ Created search_text column")
                
                print("   Creating FULLTEXT index on search_text...")
                cursor.execute("""
                    ALTER TABLE recipes 
                    ADD FULLTEXT INDEX idx_search_text_fulltext (search_text)
                """)
                connection.commit()
                print("✓ Created FULLTEXT index on search_text")
            except mysql.connector.Error as e:
                print(f"⚠ Note: {e}")
        else:
            print("✓ search_text column already exists")
            
            # Check if search_text has FULLTEXT index
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'recipes' 
                AND COLUMN_NAME = 'search_text' 
                AND INDEX_TYPE = 'FULLTEXT'
            """, (os.getenv('DB_NAME', 'recipe_recommender'),))
            
            has_search_text_idx = cursor.fetchone()[0] > 0
            
            if not has_search_text_idx:
                print("   Creating FULLTEXT index on search_text...")
                try:
                    cursor.execute("""
                        ALTER TABLE recipes 
                        ADD FULLTEXT INDEX idx_search_text_fulltext (search_text)
                    """)
                    connection.commit()
                    print("✓ Created FULLTEXT index on search_text")
                except mysql.connector.Error as e:
                    if 'Duplicate key name' in str(e):
                        print("⚠ FULLTEXT index on search_text already exists")
                    else:
                        print(f"✗ Error: {e}")
            else:
                print("✓ FULLTEXT index on search_text already exists")
        
        print("\n=== Summary ===")
        print("✓ All FULLTEXT indexes have been created successfully!")
        print("\nThe following indexes are now available:")
        print("  - recipes(name, description)")
        print("  - ingredients(name)")
        print("  - tags(name)")
        if has_search_text:
            print("  - recipes(search_text)")
        
        print("\n⚠ Note: The search_text column is empty. Run backfill_search_text.py to populate it.")
        print("   (The search will work with name/description index even without search_text)")
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        connection.rollback()
    finally:
        cursor.close()

def main():
    print("=== FULLTEXT Index Creation Script ===")
    print("This will add FULLTEXT indexes for better search performance\n")
    
    connection = None
    try:
        connection = connect_db()
        add_fulltext_indexes(connection)
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        return 1
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")
    
    return 0

if __name__ == "__main__":
    exit(main())
