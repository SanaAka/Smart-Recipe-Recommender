"""Add comments table and update ratings schema"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = conn.cursor()
    
    print("=" * 60)
    print("Adding Comments and Enhanced Ratings Schema")
    print("=" * 60)
    
    # Check if recipe_comments table exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() 
        AND table_name = 'recipe_comments'
    """)
    comments_exists = cursor.fetchone()[0] > 0
    
    if not comments_exists:
        print("\n1. Creating recipe_comments table...")
        cursor.execute("""
            CREATE TABLE recipe_comments (
                id INT PRIMARY KEY AUTO_INCREMENT,
                recipe_id INT NOT NULL,
                user_id INT NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_recipe_comments (recipe_id),
                INDEX idx_user_comments (user_id),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        print("   ✓ recipe_comments table created")
    else:
        print("\n1. ✓ recipe_comments table already exists")
    
    # Check if we need to update recipe_ratings
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_schema = DATABASE() 
        AND table_name = 'recipe_ratings' 
        AND column_name = 'created_at'
    """)
    has_timestamps = cursor.fetchone()[0] > 0
    
    if not has_timestamps:
        print("\n2. Adding timestamps to recipe_ratings...")
        cursor.execute("""
            ALTER TABLE recipe_ratings 
            ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        """)
        conn.commit()
        print("   ✓ Timestamps added to recipe_ratings")
    else:
        print("\n2. ✓ recipe_ratings already has timestamps")
    
    # Create a view for recipe stats with ratings and comments
    print("\n3. Creating/updating recipe_stats_extended view...")
    cursor.execute("DROP VIEW IF EXISTS recipe_stats_extended")
    cursor.execute("""
        CREATE VIEW recipe_stats_extended AS
        SELECT 
            r.id as recipe_id,
            COUNT(DISTINCT f.user_id) as favorite_count,
            COUNT(DISTINCT h.user_id) as cooked_count,
            COUNT(DISTINCT v.user_id) as view_count,
            AVG(rt.rating) as avg_rating,
            COUNT(DISTINCT rt.user_id) as rating_count,
            COUNT(DISTINCT c.id) as comment_count
        FROM recipes r
        LEFT JOIN user_favorites f ON r.id = f.recipe_id
        LEFT JOIN user_cooking_history h ON r.id = h.recipe_id
        LEFT JOIN user_recipe_views v ON r.id = v.recipe_id
        LEFT JOIN recipe_ratings rt ON r.id = rt.recipe_id
        LEFT JOIN recipe_comments c ON r.id = c.recipe_id
        GROUP BY r.id
    """)
    conn.commit()
    print("   ✓ recipe_stats_extended view created")
    
    print("\n" + "=" * 60)
    print("✓ Database schema updated successfully!")
    print("=" * 60)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
