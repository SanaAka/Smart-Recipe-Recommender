"""
Startup script for the Recipe Recommender backend.
Runs data initialization tasks before starting the Flask server.
"""
import mysql.connector
from mysql.connector import Error
import os
import time
import re
from dotenv import load_dotenv

load_dotenv()

# Cuisine keywords mapping for classification
CUISINE_KEYWORDS = {
    'italian': [
        'italian', 'pasta', 'spaghetti', 'lasagna', 'risotto', 'pizza', 'parmesan', 
        'mozzarella', 'pesto', 'carbonara', 'marinara', 'alfredo', 'ravioli', 
        'gnocchi', 'bruschetta', 'minestrone', 'tiramisu', 'panna cotta', 'prosciutto',
        'antipasto', 'bolognese', 'primavera', 'piccata', 'saltimbocca'
    ],
    'french': [
        'french', 'croissant', 'baguette', 'ratatouille', 'bouillabaisse', 
        'coq au vin', 'crepe', 'quiche', 'souffle', 'bechamel', 'cassoulet',
        'nicoise', 'provencal', 'bourguignon', 'gratin', 'au gratin'
    ],
    'mexican': [
        'mexican', 'taco', 'burrito', 'enchilada', 'quesadilla', 'salsa', 
        'guacamole', 'tortilla', 'fajita', 'chimichanga', 'nachos', 'mole',
        'tamale', 'carnitas', 'ceviche', 'jalapeno', 'cilantro', 'chipotle',
        'tex mex', 'tex-mex'
    ],
    'chinese': [
        'chinese', 'stir fry', 'stir-fry', 'wonton', 'dumpling', 'chow mein', 'lo mein',
        'kung pao', 'szechuan', 'sichuan', 'fried rice', 'egg roll', 
        'spring roll', 'dim sum', 'hot and sour', 'sweet and sour', 'general tso',
        'orange chicken', 'hoisin', 'char siu', 'wok'
    ],
    'japanese': [
        'japanese', 'sushi', 'sashimi', 'tempura', 'ramen', 'udon', 'soba',
        'teriyaki', 'miso', 'wasabi', 'edamame', 'yakitori', 'tonkatsu',
        'hibachi', 'bento', 'sake', 'gyoza', 'katsu', 'donburi'
    ],
    'indian': [
        'indian', 'curry', 'tandoori', 'tikka', 'masala', 'biryani', 'naan',
        'samosa', 'pakora', 'chutney', 'vindaloo', 'korma', 'dal', 'paneer',
        'garam masala', 'turmeric', 'cumin', 'cardamom', 'butter chicken',
        'saag', 'palak', 'dosa', 'idli', 'chana'
    ],
    'thai': [
        'thai', 'pad thai', 'tom yum', 'tom kha', 'green curry', 'red curry', 
        'panang', 'satay', 'lemongrass', 'galangal', 'thai basil', 
        'coconut curry', 'massaman', 'papaya salad', 'larb'
    ],
    'korean': [
        'korean', 'kimchi', 'bulgogi', 'bibimbap', 'gochujang', 'galbi',
        'japchae', 'tteokbokki', 'ddukbokki', 'korean bbq', 'gochugaru',
        'ssam', 'banchan', 'jjigae', 'kimbap', 'sundubu', 'samgyeopsal',
        'dakgalbi', 'bossam', 'dongchimi', 'doenjang'
    ],
    'greek': [
        'greek', 'gyro', 'souvlaki', 'moussaka', 'tzatziki', 'feta', 
        'spanakopita', 'baklava', 'dolma', 'ouzo', 'oregano', 'kalamata',
        'pita', 'lamb greek'
    ],
    'spanish': [
        'spanish', 'paella', 'tapas', 'gazpacho', 'chorizo', 'sangria',
        'tortilla espanola', 'manchego', 'serrano', 'patatas bravas'
    ],
    'middle_eastern': [
        'middle eastern', 'hummus', 'falafel', 'shawarma', 'kebab', 'tahini',
        'baba ganoush', 'tabbouleh', 'pita', "za'atar", 'zaatar', 'sumac',
        'lebanese', 'persian', 'turkish', 'harissa'
    ],
    'vietnamese': [
        'vietnamese', 'pho', 'banh mi', 'spring roll', 'fish sauce', 
        'rice noodle', 'bun', 'vermicelli', 'lemongrass', 'nuoc cham'
    ],
    'american': [
        'hamburger', 'burger', 'hot dog', 'bbq', 'barbecue', 'pulled pork', 
        'coleslaw', 'fried chicken', 'mac and cheese', 'apple pie', 'brownies', 
        'meatloaf', 'pot roast', 'casserole', 'buffalo wing', 'southern', 'cajun'
    ],
    'mediterranean': [
        'mediterranean', 'olive oil', 'chickpea', 'couscous', 'lentil',
        'tahini', 'pomegranate', 'eggplant'
    ],
    'caribbean': [
        'caribbean', 'jerk', 'plantain', 'rum cake', 'allspice', 
        'scotch bonnet', 'jamaican', 'cuban'
    ]
}

def connect_db():
    """Connect to MySQL database with retry logic"""
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', '3306'))
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    database = os.getenv('DB_NAME', 'recipe_recommender')
    
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            print(f"[STARTUP] Connected to database successfully")
            return conn
        except Error as e:
            if attempt < max_retries - 1:
                print(f"[STARTUP] Database connection attempt {attempt + 1} failed, retrying in {retry_delay}s... ({e})")
                time.sleep(retry_delay)
            else:
                print(f"[STARTUP] Failed to connect to database after {max_retries} attempts")
                raise

def ensure_cuisine_column():
    """Ensure cuisine column exists in recipes table"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'recipes' 
            AND COLUMN_NAME = 'cuisine'
        """, (os.getenv('DB_NAME', 'recipe_recommender'),))
        
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            print("[STARTUP] Adding cuisine column to recipes table...")
            cursor.execute("""
                ALTER TABLE recipes 
                ADD COLUMN cuisine VARCHAR(100) DEFAULT NULL,
                ADD INDEX idx_cuisine (cuisine)
            """)
            conn.commit()
            print("[STARTUP] ✓ Cuisine column added")
        else:
            print("[STARTUP] ✓ Cuisine column already exists")
            
    except Exception as e:
        print(f"[STARTUP] Error adding cuisine column: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def classify_cuisine(name, ingredients_str):
    """Classify cuisine based on recipe name and ingredients"""
    text = (name + ' ' + ingredients_str).lower()
    
    scores = {}
    for cuisine, keywords in CUISINE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                score += 1
        if score > 0:
            scores[cuisine] = score
    
    if scores:
        return max(scores, key=scores.get)
    return None

def classify_cuisines():
    """Classify cuisine for all unclassified recipes"""
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check how many need classification
        cursor.execute("SELECT COUNT(*) as count FROM recipes WHERE cuisine IS NULL")
        unclassified = cursor.fetchone()['count']
        
        if unclassified == 0:
            print("[STARTUP] ✓ All recipes already have cuisine classification")
            return
        
        print(f"[STARTUP] Classifying cuisine for {unclassified} recipes...")
        
        # Fetch recipes with ingredients (only unclassified)
        cursor.execute("""
            SELECT 
                r.id, 
                r.name,
                GROUP_CONCAT(i.name SEPARATOR ' ') as ingredients
            FROM recipes r
            LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE r.cuisine IS NULL
            GROUP BY r.id, r.name
        """)
        
        recipes = cursor.fetchall()
        
        update_cursor = conn.cursor()
        classified_count = 0
        batch_size = 500
        batch_updates = []
        
        for idx, recipe in enumerate(recipes):
            cuisine = classify_cuisine(recipe['name'] or '', recipe['ingredients'] or '')
            
            if cuisine:
                batch_updates.append((cuisine, recipe['id']))
                classified_count += 1
            
            # Execute batch updates
            if len(batch_updates) >= batch_size:
                update_cursor.executemany(
                    "UPDATE recipes SET cuisine = %s WHERE id = %s",
                    batch_updates
                )
                conn.commit()
                batch_updates = []
                print(f"[STARTUP] Processed {idx + 1}/{len(recipes)} recipes...")
        
        # Execute remaining updates
        if batch_updates:
            update_cursor.executemany(
                "UPDATE recipes SET cuisine = %s WHERE id = %s",
                batch_updates
            )
            conn.commit()
        
        update_cursor.close()
        
        print(f"[STARTUP] ✓ Classified {classified_count}/{len(recipes)} recipes")
        
        # Show cuisine distribution
        cursor.execute("""
            SELECT cuisine, COUNT(*) as count 
            FROM recipes 
            WHERE cuisine IS NOT NULL 
            GROUP BY cuisine 
            ORDER BY count DESC
            LIMIT 20
        """)
        
        print("[STARTUP] Cuisine Distribution:")
        for row in cursor.fetchall():
            print(f"  {row['cuisine']:20s}: {row['count']:,}")
        
    except Exception as e:
        print(f"[STARTUP] Error classifying cuisines: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def add_cuisine_tags():
    """Add cuisine tags to recipes based on classification"""
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get existing tags
        cursor.execute("SELECT id, name FROM tags")
        existing_tags = {tag['name'].lower(): tag['id'] for tag in cursor.fetchall()}
        
        # Get distinct cuisines
        cursor.execute("SELECT DISTINCT cuisine FROM recipes WHERE cuisine IS NOT NULL")
        cuisines = [row['cuisine'] for row in cursor.fetchall()]
        
        cuisine_tag_ids = {}
        
        # Ensure tags exist for each cuisine
        for cuisine in cuisines:
            cuisine_title = cuisine.replace('_', ' ').title()
            cuisine_lower = cuisine_title.lower()
            
            if cuisine_lower not in existing_tags:
                cursor.execute("INSERT INTO tags (name) VALUES (%s)", (cuisine_title,))
                conn.commit()
                tag_id = cursor.lastrowid
                existing_tags[cuisine_lower] = tag_id
                print(f"[STARTUP] Created tag: {cuisine_title}")
            
            cuisine_tag_ids[cuisine] = existing_tags[cuisine_lower]
        
        # Add tags to recipes that don't have them
        for cuisine, tag_id in cuisine_tag_ids.items():
            cursor.execute("""
                INSERT IGNORE INTO recipe_tags (recipe_id, tag_id)
                SELECT r.id, %s
                FROM recipes r
                WHERE r.cuisine = %s
                AND NOT EXISTS (
                    SELECT 1 FROM recipe_tags rt 
                    WHERE rt.recipe_id = r.id AND rt.tag_id = %s
                )
            """, (tag_id, cuisine, tag_id))
        
        conn.commit()
        print("[STARTUP] ✓ Cuisine tags added to recipes")
        
    except Exception as e:
        print(f"[STARTUP] Error adding cuisine tags: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def run_startup_tasks():
    """Run all startup initialization tasks"""
    print("=" * 60)
    print("[STARTUP] Recipe Recommender Backend Initialization")
    print("=" * 60)
    
    # Wait a bit for database to be fully ready
    time.sleep(2)
    
    try:
        ensure_cuisine_column()
        classify_cuisines()
        add_cuisine_tags()
        print("=" * 60)
        print("[STARTUP] ✓ Initialization complete!")
        print("=" * 60)
    except Exception as e:
        print(f"[STARTUP] Initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_startup_tasks()
