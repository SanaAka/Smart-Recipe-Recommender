import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'smart_recipe_db')
}

# Cuisine mapping based on recipe names and ingredients
cuisine_keywords = {
    'Italian': ['pasta', 'pizza', 'lasagna', 'risotto', 'parmesan', 'mozzarella', 'marinara', 'pesto', 'tiramisu', 'carbonara', 'alfredo', 'italian', 'ravioli', 'gnocchi', 'focaccia', 'bruschetta', 'caprese', 'minestrone'],
    'Mexican': ['taco', 'burrito', 'enchilada', 'salsa', 'guacamole', 'quesadilla', 'tortilla', 'chimichanga', 'fajita', 'nacho', 'mexican', 'jalapeño', 'cilantro lime', 'chipotle', 'carnitas', 'tamale', 'mole'],
    'Chinese': ['stir fry', 'fried rice', 'chow mein', 'spring roll', 'dumpling', 'wonton', 'chinese', 'szechuan', 'kung pao', 'sweet and sour', 'orange chicken', 'lo mein', 'egg roll', 'general tso', 'sesame', 'hoisin'],
    'Indian': ['curry', 'tandoori', 'tikka', 'masala', 'biryani', 'naan', 'samosa', 'indian', 'garam masala', 'turmeric', 'cumin', 'coriander', 'cardamom', 'vindaloo', 'korma', 'dal', 'chutney'],
    'Japanese': ['sushi', 'ramen', 'teriyaki', 'tempura', 'miso', 'soba', 'udon', 'japanese', 'wasabi', 'edamame', 'sake', 'katsu', 'yakitori', 'gyoza', 'donburi', 'bento'],
    'French': ['croissant', 'baguette', 'quiche', 'crepe', 'souffle', 'french', 'brie', 'champagne', 'ratatouille', 'bouillabaisse', 'coq au vin', 'cassoulet', 'croque', 'escargot', 'mousse'],
    'Greek': ['gyro', 'souvlaki', 'tzatziki', 'feta', 'greek', 'moussaka', 'spanakopita', 'baklava', 'dolma', 'hummus', 'pita', 'olive', 'oregano', 'lemon greek'],
    'Spanish': ['paella', 'tapas', 'gazpacho', 'chorizo', 'spanish', 'sangria', 'tortilla española', 'patatas bravas', 'jamón', 'manchego'],
    'American': ['burger', 'hot dog', 'bbq', 'barbecue', 'mac and cheese', 'fried chicken', 'meatloaf', 'apple pie', 'coleslaw', 'cornbread', 'biscuit', 'gravy', 'southern', 'cajun', 'tex mex', 'buffalo'],
    'Mediterranean': ['hummus', 'falafel', 'tabbouleh', 'mediterranean', 'olive oil', 'chickpea', 'tahini', 'za\'atar', 'sumac', 'pomegranate'],
    'Korean': ['kimchi', 'bulgogi', 'bibimbap', 'korean', 'gochujang', 'ssam', 'japchae', 'galbi', 'tteokbokki'],
    'Vietnamese': ['pho', 'banh mi', 'spring roll vietnamese', 'vietnamese', 'fish sauce', 'rice noodle'],
    'Middle Eastern': ['shawarma', 'kebab', 'falafel', 'baba ganoush', 'couscous', 'harissa', 'ras el hanout', 'persian', 'lebanese', 'turkish'],
    'Caribbean': ['jerk', 'caribbean', 'plantain', 'mango', 'rum', 'coconut caribbean', 'allspice', 'scotch bonnet'],
    'Asian Fusion': ['asian', 'oriental', 'fusion'],
}

print("Connecting to database...")
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

# Get all recipes
print("Loading recipes...")
cursor.execute("SELECT id, name FROM recipes")
recipes = cursor.fetchall()
print(f"Found {len(recipes)} recipes")

# Get existing tags to find cuisine tags
cursor.execute("SELECT id, name FROM tags")
existing_tags = {tag['name'].lower(): tag['id'] for tag in cursor.fetchall()}

cuisine_tag_ids = {}
cuisines_added = 0

print("\nAdding cuisine tags...")

# Add cuisine tags if they don't exist
for cuisine in cuisine_keywords.keys():
    cuisine_lower = cuisine.lower()
    if cuisine_lower not in existing_tags:
        cursor.execute("INSERT INTO tags (name) VALUES (%s)", (cuisine,))
        conn.commit()
        tag_id = cursor.lastrowid
        cuisine_tag_ids[cuisine] = tag_id
        existing_tags[cuisine_lower] = tag_id
        print(f"  Created tag: {cuisine}")
    else:
        cuisine_tag_ids[cuisine] = existing_tags[cuisine_lower]
        print(f"  Using existing tag: {cuisine}")

# Analyze each recipe and assign cuisine tags
print("\nAnalyzing recipes and assigning cuisines...")
recipes_tagged = 0

for idx, recipe in enumerate(recipes):
    if idx % 10000 == 0:
        print(f"  Processing recipe {idx:,}/{len(recipes):,}...")
    
    recipe_name = recipe['name'].lower()
    matched_cuisines = []
    
    # Check which cuisines match this recipe
    for cuisine, keywords in cuisine_keywords.items():
        for keyword in keywords:
            if keyword in recipe_name:
                matched_cuisines.append(cuisine)
                break
    
    # Add cuisine tags to recipe
    if matched_cuisines:
        for cuisine in matched_cuisines:
            tag_id = cuisine_tag_ids[cuisine]
            # Check if relationship already exists
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM recipe_tags 
                WHERE recipe_id = %s AND tag_id = %s
            """, (recipe['id'], tag_id))
            
            if cursor.fetchone()['count'] == 0:
                cursor.execute("""
                    INSERT INTO recipe_tags (recipe_id, tag_id)
                    VALUES (%s, %s)
                """, (recipe['id'], tag_id))
        
        recipes_tagged += 1
        
        # Commit every 1000 recipes for better performance
        if idx % 1000 == 0:
            conn.commit()

# Final commit
conn.commit()

print(f"\n✓ Successfully tagged {recipes_tagged} recipes with cuisines")

# Show statistics
print("\nCuisine distribution:")
for cuisine, tag_id in cuisine_tag_ids.items():
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM recipe_tags
        WHERE tag_id = %s
    """, (tag_id,))
    count = cursor.fetchone()['count']
    print(f"  {cuisine}: {count} recipes")

cursor.close()
conn.close()

print("\n✓ Done! Cuisine tags have been added to the database.")
