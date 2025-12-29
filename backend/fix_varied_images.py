"""
Assign varied placeholder images based on recipe names/categories
This gives visual variety until you get actual recipe photos
"""

import mysql.connector, os, re
from dotenv import load_dotenv

load_dotenv()

# Food category mappings to image keywords
FOOD_CATEGORIES = {
    'chicken': ['chicken', 'poultry'],
    'beef': ['beef', 'steak', 'burger', 'meatball', 'meat loaf'],
    'pork': ['pork', 'bacon', 'ham', 'sausage'],
    'fish': ['fish', 'salmon', 'tuna', 'seafood', 'shrimp', 'crab'],
    'pasta': ['pasta', 'spaghetti', 'lasagne', 'noodle', 'macaroni'],
    'salad': ['salad', 'coleslaw'],
    'soup': ['soup', 'stew', 'chili', 'broth'],
    'dessert': ['cake', 'pie', 'cookie', 'brownie', 'fudge', 'candy', 'pudding', 'dessert'],
    'bread': ['bread', 'roll', 'biscuit', 'muffin', 'scone'],
    'rice': ['rice', 'risotto'],
    'vegetable': ['broccoli', 'corn', 'potato', 'carrot', 'squash', 'zucchini', 'pepper', 'bean'],
    'cheese': ['cheese', 'queso'],
    'dip': ['dip'],
    'casserole': ['casserole'],
    'pizza': ['pizza'],
}

def categorize_recipe(name):
    """Determine recipe category from name"""
    name_lower = name.lower()
    
    for category, keywords in FOOD_CATEGORIES.items():
        for keyword in keywords:
            if keyword in name_lower:
                return category
    
    return 'food'  # default

def get_image_for_recipe(recipe_id, recipe_name):
    """Generate appropriate image URL for recipe"""
    category = categorize_recipe(recipe_name)
    
    # Use Unsplash with specific food category for better variety
    return f"https://source.unsplash.com/400x300/?{category},food,dish"

def update_recipe_images():
    """Update all recipes with category-appropriate images"""
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    
    cursor = conn.cursor(dictionary=True)
    
    # Get all recipes
    print("Fetching recipes...")
    cursor.execute("SELECT id, name FROM recipes")
    recipes = cursor.fetchall()
    
    print(f"Updating {len(recipes):,} recipes with category-based images...")
    
    update_cursor = conn.cursor()
    batch_size = 1000
    count = 0
    
    for recipe in recipes:
        image_url = get_image_for_recipe(recipe['id'], recipe['name'])
        
        update_cursor.execute("""
            UPDATE recipes 
            SET image_url = %s 
            WHERE id = %s
        """, (image_url, recipe['id']))
        
        count += 1
        
        if count % batch_size == 0:
            conn.commit()
            print(f"  Updated {count:,}/{len(recipes):,} recipes...")
    
    conn.commit()
    
    print(f"\n✅ Successfully updated {count:,} recipes with varied images!")
    print("\nCategories used: chicken, beef, pork, fish, pasta, salad, soup,")
    print("dessert, bread, rice, vegetables, cheese, dip, casserole, pizza, etc.")
    
    update_cursor.close()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    update_recipe_images()
