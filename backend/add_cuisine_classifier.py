"""
Add cuisine classification to recipes based on name and ingredient analysis
"""
import mysql.connector
import os
from dotenv import load_dotenv
import re

load_dotenv()

# Cuisine keywords mapping
CUISINE_KEYWORDS = {
    'italian': [
        'italian', 'pasta', 'spaghetti', 'lasagna', 'risotto', 'pizza', 'parmesan', 
        'mozzarella', 'pesto', 'carbonara', 'marinara', 'alfredo', 'ravioli', 
        'gnocchi', 'bruschetta', 'minestrone', 'tiramisu', 'panna cotta'
    ],
    'french': [
        'french', 'croissant', 'baguette', 'ratatouille', 'bouillabaisse', 
        'coq au vin', 'crepe', 'quiche', 'souffle', 'bechamel', 'cassoulet',
        'nicoise', 'provencal', 'bourguignon', 'gratin'
    ],
    'mexican': [
        'mexican', 'taco', 'burrito', 'enchilada', 'quesadilla', 'salsa', 
        'guacamole', 'tortilla', 'fajita', 'chimichanga', 'nachos', 'mole',
        'tamale', 'carnitas', 'ceviche', 'jalapeno', 'cilantro', 'chipotle'
    ],
    'chinese': [
        'chinese', 'stir fry', 'wonton', 'dumpling', 'chow mein', 'lo mein',
        'kung pao', 'szechuan', 'teriyaki', 'fried rice', 'egg roll', 
        'spring roll', 'dim sum', 'hot and sour', 'sweet and sour'
    ],
    'japanese': [
        'japanese', 'sushi', 'sashimi', 'tempura', 'ramen', 'udon', 'soba',
        'teriyaki', 'miso', 'wasabi', 'edamame', 'yakitori', 'tonkatsu',
        'hibachi', 'bento', 'sake'
    ],
    'indian': [
        'indian', 'curry', 'tandoori', 'tikka', 'masala', 'biryani', 'naan',
        'samosa', 'pakora', 'chutney', 'vindaloo', 'korma', 'dal', 'paneer',
        'garam masala', 'turmeric', 'cumin', 'cardamom'
    ],
    'thai': [
        'thai', 'pad thai', 'tom yum', 'green curry', 'red curry', 
        'panang', 'satay', 'lemongrass', 'galangal', 'basil thai', 
        'coconut milk thai'
    ],
    'korean': [
        'korean', 'kimchi', 'bulgogi', 'bibimbap', 'gochujang', 'galbi',
        'japchae', 'ddukbokki', 'korean bbq', 'gochugaru'
    ],
    'greek': [
        'greek', 'gyro', 'souvlaki', 'moussaka', 'tzatziki', 'feta', 
        'spanakopita', 'baklava', 'dolma', 'ouzo', 'oregano greek'
    ],
    'spanish': [
        'spanish', 'paella', 'tapas', 'gazpacho', 'chorizo', 'sangria',
        'tortilla espanola', 'manchego', 'serrano'
    ],
    'middle_eastern': [
        'middle eastern', 'hummus', 'falafel', 'shawarma', 'kebab', 'tahini',
        'baba ganoush', 'tabbouleh', 'pita', 'za\'atar', 'sumac'
    ],
    'american': [
        'hamburger', 'hot dog', 'bbq', 'barbecue', 'pulled pork', 'coleslaw',
        'fried chicken', 'mac and cheese', 'apple pie', 'brownies', 'meatloaf',
        'pot roast', 'casserole'
    ]
}

def connect_db():
    """Connect to MySQL database"""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'recipe_recommender')
    )

def add_cuisine_column():
    """Add cuisine column to recipes table if it doesn't exist"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'recipes' 
            AND COLUMN_NAME = 'cuisine'
        """, (os.getenv('DB_NAME', 'recipe_recommender'),))
        
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            print("Adding cuisine column to recipes table...")
            cursor.execute("""
                ALTER TABLE recipes 
                ADD COLUMN cuisine VARCHAR(100) DEFAULT NULL,
                ADD INDEX idx_cuisine (cuisine)
            """)
            conn.commit()
            print("✓ Cuisine column added successfully")
        else:
            print("✓ Cuisine column already exists")
            
    except Exception as e:
        print(f"Error adding column: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def classify_cuisine(name, ingredients_str):
    """Classify cuisine based on recipe name and ingredients"""
    text = (name + ' ' + ingredients_str).lower()
    
    # Score each cuisine
    scores = {}
    for cuisine, keywords in CUISINE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # Use word boundaries for more accurate matching
            if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                score += 1
        if score > 0:
            scores[cuisine] = score
    
    # Return cuisine with highest score
    if scores:
        return max(scores, key=scores.get)
    return None

def classify_all_recipes():
    """Classify cuisine for all recipes"""
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all recipes with ingredients
        print("Fetching recipes...")
        cursor.execute("""
            SELECT 
                r.id, 
                r.name,
                GROUP_CONCAT(i.name SEPARATOR ' ') as ingredients
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            GROUP BY r.id, r.name
        """)
        
        recipes = cursor.fetchall()
        print(f"Found {len(recipes)} recipes to classify")
        
        # Classify and update
        update_cursor = conn.cursor()
        classified_count = 0
        
        for idx, recipe in enumerate(recipes):
            if idx % 1000 == 0:
                print(f"Processed {idx}/{len(recipes)} recipes...")
            
            cuisine = classify_cuisine(
                recipe['name'] or '', 
                recipe['ingredients'] or ''
            )
            
            if cuisine:
                update_cursor.execute(
                    "UPDATE recipes SET cuisine = %s WHERE id = %s",
                    (cuisine, recipe['id'])
                )
                classified_count += 1
        
        conn.commit()
        print(f"\n✓ Successfully classified {classified_count}/{len(recipes)} recipes")
        
        # Show cuisine distribution
        cursor.execute("""
            SELECT cuisine, COUNT(*) as count 
            FROM recipes 
            WHERE cuisine IS NOT NULL 
            GROUP BY cuisine 
            ORDER BY count DESC
        """)
        
        print("\nCuisine Distribution:")
        print("-" * 40)
        for row in cursor.fetchall():
            print(f"  {row['cuisine']:20s}: {row['count']:,}")
        
    except Exception as e:
        print(f"Error classifying recipes: {e}")
        conn.rollback()
    finally:
        cursor.close()
        update_cursor.close()
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Cuisine Classification System")
    print("=" * 60)
    
    add_cuisine_column()
    classify_all_recipes()
    
    print("\n" + "=" * 60)
    print("Classification complete!")
    print("=" * 60)
