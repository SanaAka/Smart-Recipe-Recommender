"""
Backfill `recipes.search_text` for existing data.
This script computes search_text by concatenating recipe name, ingredients and tags.
Run once after creating the `search_text` column and indexes.
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'recipe_recommender')
    )

    cursor = conn.cursor()

    # Ensure the `search_text` column exists; create it if possible
    try:
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='recipes' AND COLUMN_NAME='search_text'")
        exists = cursor.fetchone()[0] > 0
    except Exception:
        exists = False

    if not exists:
        print("`search_text` column not found on `recipes` table. Attempting to create it...")
        try:
            cursor.execute("ALTER TABLE recipes ADD COLUMN search_text TEXT")
            conn.commit()
            print("Created `search_text` column.")
        except Exception as e:
            print("Failed to create `search_text` column automatically:", e)
            print("Please run the ALTER TABLE command manually or ensure your DB user has ALTER privileges.")
            cursor.close()
            conn.close()
            return

    # Increase GROUP_CONCAT max length for this session to avoid truncation errors
    try:
        cursor.execute("SET SESSION group_concat_max_len = 4194304")
        # Also increase group_concat_max_len for the client connection if needed
    except Exception:
        pass

    # This update uses subqueries to aggregate ingredients and tags per recipe.
    update_sql = """
    UPDATE recipes r
    LEFT JOIN (
        SELECT ri.recipe_id, GROUP_CONCAT(i.name SEPARATOR ' ') as ings
        FROM recipe_ingredients ri
        JOIN ingredients i ON ri.ingredient_id = i.id
        GROUP BY ri.recipe_id
    ) ing ON r.id = ing.recipe_id
    LEFT JOIN (
        SELECT rt.recipe_id, GROUP_CONCAT(t.name SEPARATOR ' ') as tgs
        FROM recipe_tags rt
        JOIN tags t ON rt.tag_id = t.id
        GROUP BY rt.recipe_id
    ) tg ON r.id = tg.recipe_id
    SET r.search_text = TRIM(CONCAT(IFNULL(LOWER(r.name), ''), ' ', IFNULL(ing.ings, ''), ' ', IFNULL(tg.tgs, '')))
    WHERE r.search_text IS NULL OR r.search_text = ''
    """

    print("Running backfill update for search_text (may take a while)…")
    cursor.execute(update_sql)
    conn.commit()
    print(f"Backfill complete, rows affected: {cursor.rowcount}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
