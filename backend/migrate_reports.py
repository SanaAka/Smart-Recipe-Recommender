"""Migration: Add user_reports table and suspended_until column."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import mysql.connector
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

c = mysql.connector.connect(
    host='127.0.0.1', user='root',
    password=os.getenv('DB_PASSWORD'),
    database='recipe_recommender'
)
cur = c.cursor()

# 1. Add suspended_until column to users
cur.execute(
    "SELECT COUNT(*) FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA='recipe_recommender' AND TABLE_NAME='users' AND COLUMN_NAME='suspended_until'"
)
if cur.fetchone()[0] == 0:
    cur.execute('ALTER TABLE users ADD COLUMN suspended_until DATETIME NULL DEFAULT NULL')
    print('Added suspended_until column to users')
else:
    print('suspended_until column already exists')

# 2. Create user_reports table
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_reports (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reporter_id INT NOT NULL,
        reported_user_id INT NOT NULL,
        reason VARCHAR(50) NOT NULL,
        description TEXT,
        status ENUM('pending','reviewed','resolved','dismissed') DEFAULT 'pending',
        admin_notes TEXT,
        resolved_by INT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        resolved_at DATETIME NULL,
        FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (reported_user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL,
        INDEX idx_status (status),
        INDEX idx_reported_user (reported_user_id),
        INDEX idx_created (created_at)
    )
""")
print('user_reports table ready')

c.commit()
cur.close()
c.close()
print('Migration complete!')
