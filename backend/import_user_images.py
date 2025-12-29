"""
Import recipe images from user's CSV file
Handles flexible column naming (id/recipe_id, img URL/image_url)
"""

import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def import_images_from_csv(csv_path):
    """Import recipe images from CSV file"""
    try:
        # Read CSV
        print(f"Reading CSV from: {csv_path}")
        df = pd.read_csv(csv_path)
        
        print(f"CSV columns: {list(df.columns)}")
        
        # Handle different column names
        # Try to find ID column
        id_col = None
        for col in ['id', 'recipe_id', 'ID', 'Recipe ID']:
            if col in df.columns:
                id_col = col
                break
        
        # Try to find image URL column
        img_col = None
        for col in ['image_url', 'img URL', 'img_url', 'imageUrl', 'Image URL']:
            if col in df.columns:
                img_col = col
                break
        
        if not id_col or not img_col:
            print(f"❌ Could not find required columns.")
            print(f"   Available columns: {list(df.columns)}")
            print(f"   Need: 'id' (or 'recipe_id') and 'image_url' (or 'img URL')")
            return
        
        print(f"✓ Found ID column: '{id_col}'")
        print(f"✓ Found Image URL column: '{img_col}'")
        
        # Clean data - remove rows with empty URLs
        df = df[[id_col, img_col]].dropna()
        df = df[df[img_col].str.strip() != '']
        
        print(f"✓ Loaded {len(df)} recipe images from CSV")
        
        # Connect to database
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', '127.0.0.1'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'recipe_recommender')
        )
        
        cursor = conn.cursor()
        
        # Update each recipe
        updated = 0
        not_found = 0
        
        for idx, row in df.iterrows():
            recipe_id = int(row[id_col])
            image_url = str(row[img_col]).strip()
            
            cursor.execute("""
                UPDATE recipes 
                SET image_url = %s 
                WHERE id = %s
            """, (image_url, recipe_id))
            
            if cursor.rowcount > 0:
                updated += 1
            else:
                not_found += 1
                if not_found <= 5:  # Show first 5 not found
                    print(f"  Recipe ID {recipe_id} not found in database")
        
        conn.commit()
        
        print(f"\n✅ Successfully updated {updated} recipes with your image URLs!")
        if not_found > 0:
            print(f"⚠️  {not_found} recipe IDs were not found in the database")
        
        cursor.close()
        conn.close()
        
    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")
        print("Please provide the correct path to your CSV file")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python import_user_images.py <path_to_csv>")
        print("\nExample:")
        print('  python import_user_images.py "C:\\Users\\HTPP\\Desktop\\data.csv"')
        print("\nYour CSV should have:")
        print("  - Column: 'id' or 'recipe_id'")
        print("  - Column: 'image_url' or 'img URL'")
    else:
        csv_file = sys.argv[1]
        import_images_from_csv(csv_file)
