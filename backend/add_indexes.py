"""Add database indexes for improved query performance"""
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

print("Adding database indexes for performance optimization...")
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

indexes = [
    ("idx_recipe_name", "recipes", "name(255)"),
    ("idx_recipe_minutes", "recipes", "minutes"),
    ("idx_ingredient_name", "ingredients", "name(255)"),
    ("idx_tag_name", "tags", "name(255)"),
    ("idx_recipe_ingredients_recipe", "recipe_ingredients", "recipe_id"),
    ("idx_recipe_ingredients_ingredient", "recipe_ingredients", "ingredient_id"),
    ("idx_recipe_tags_recipe", "recipe_tags", "recipe_id"),
    ("idx_recipe_tags_tag", "recipe_tags", "tag_id"),
    ("idx_nutrition_recipe", "nutrition", "recipe_id"),
    ("idx_nutrition_calories", "nutrition", "calories"),
    ("idx_steps_recipe", "steps", "recipe_id")
]

for idx_name, table, column in indexes:
    try:
        # Check if index exists
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.statistics 
            WHERE table_schema = DATABASE() 
            AND table_name = '{table}' 
            AND index_name = '{idx_name}'
        """)
        
        if cursor.fetchone()[0] == 0:
            print(f"  Creating index {idx_name} on {table}({column})...")
            cursor.execute(f"CREATE INDEX {idx_name} ON {table}({column})")
            conn.commit()
            print(f"  ✓ Created {idx_name}")
        else:
            print(f"  ✓ Index {idx_name} already exists")
    except Exception as e:
        print(f"  ✗ Error creating {idx_name}: {e}")

cursor.close()
conn.close()
print("\n✓ Database indexing complete! Queries will be much faster now.")
