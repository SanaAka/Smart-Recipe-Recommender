"""
Migration script for v3 features:
1. Comment replies
2. Comment reactions (like/dislike)
3. User-posted recipes
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'recipe_recommender'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
}

MIGRATIONS = [
    # 1. Comment replies table
    """
    CREATE TABLE IF NOT EXISTS comment_replies (
        id INT AUTO_INCREMENT PRIMARY KEY,
        comment_id INT NOT NULL,
        user_id INT NOT NULL,
        reply TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (comment_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_reply_comment (comment_id),
        INDEX idx_reply_user (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # 2. Comment reactions table (like/dislike)
    """
    CREATE TABLE IF NOT EXISTS comment_reactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        comment_id INT NOT NULL,
        user_id INT NOT NULL,
        reaction_type ENUM('like', 'dislike') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_user_comment (comment_id, user_id),
        FOREIGN KEY (comment_id) REFERENCES recipe_comments(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_reaction_comment (comment_id),
        INDEX idx_reaction_user (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # 3. Reply reactions table (like/dislike on replies too)
    """
    CREATE TABLE IF NOT EXISTS reply_reactions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reply_id INT NOT NULL,
        user_id INT NOT NULL,
        reaction_type ENUM('like', 'dislike') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_user_reply (reply_id, user_id),
        FOREIGN KEY (reply_id) REFERENCES comment_replies(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_rreaction_reply (reply_id),
        INDEX idx_rreaction_user (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # 4. Add submitted_by column to recipes table for user-posted recipes
    """
    ALTER TABLE recipes
        ADD COLUMN IF NOT EXISTS submitted_by INT NULL DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS is_approved TINYINT(1) DEFAULT 1,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
    """,

    # 5. Index for user-submitted recipes
    """
    CREATE INDEX IF NOT EXISTS idx_recipes_submitted_by ON recipes(submitted_by)
    """,
]


def run_migrations():
    print("Connecting to database...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for i, sql in enumerate(MIGRATIONS, 1):
        try:
            print(f"Running migration {i}/{len(MIGRATIONS)}...")
            cursor.execute(sql.strip())
            conn.commit()
            print(f"  ✓ Migration {i} succeeded")
        except mysql.connector.Error as e:
            # Ignore "already exists" or "duplicate column" errors
            err_code = e.errno
            if err_code in (1060, 1061, 1062, 1068, 1050, 1061):
                print(f"  ✓ Migration {i} skipped (already applied): {e.msg}")
                conn.rollback()
            else:
                print(f"  ✗ Migration {i} failed: {e}")
                conn.rollback()

    cursor.close()
    conn.close()
    print("\n✅ All v3 migrations complete!")


if __name__ == '__main__':
    run_migrations()
