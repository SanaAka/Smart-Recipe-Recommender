"""
Database schema for 8 unique standout features
Run this script to create all necessary tables
"""
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
    
    print("=" * 70)
    print("Creating Tables for 8 Unique Features")
    print("=" * 70)
    
    # 1. Ingredient Expiry Tracker
    print("\n1. Creating ingredient_inventory table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredient_inventory (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            ingredient_name VARCHAR(255) NOT NULL,
            quantity DECIMAL(10,2),
            unit VARCHAR(50),
            purchase_date DATE,
            expiry_date DATE,
            location VARCHAR(100) DEFAULT 'fridge',
            notes TEXT,
            status ENUM('fresh', 'expiring_soon', 'expired') DEFAULT 'fresh',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_ingredients (user_id),
            INDEX idx_expiry_date (expiry_date),
            INDEX idx_status (status),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("   ✓ ingredient_inventory created")
    
    # 2. Nutrition Goals Tracker
    print("\n2. Creating nutrition_goals and nutrition_logs tables...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_goals (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            goal_type ENUM('daily', 'weekly') DEFAULT 'daily',
            calories_target INT,
            protein_target DECIMAL(10,2),
            carbs_target DECIMAL(10,2),
            fat_target DECIMAL(10,2),
            sodium_target DECIMAL(10,2),
            sugar_target DECIMAL(10,2),
            fiber_target DECIMAL(10,2),
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_active_goal (user_id, goal_type, active)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_logs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            recipe_id INT,
            meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack') DEFAULT 'lunch',
            servings DECIMAL(4,2) DEFAULT 1.0,
            calories DECIMAL(10,2),
            protein DECIMAL(10,2),
            carbs DECIMAL(10,2),
            fat DECIMAL(10,2),
            sodium DECIMAL(10,2),
            sugar DECIMAL(10,2),
            log_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_date (user_id, log_date),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE SET NULL
        )
    """)
    print("   ✓ nutrition_goals and nutrition_logs created")
    
    # 3. Recipe Difficulty & Skills
    print("\n3. Creating recipe_difficulty and user_cooking_skills tables...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipe_difficulty (
            id INT PRIMARY KEY AUTO_INCREMENT,
            recipe_id INT NOT NULL,
            difficulty_score DECIMAL(3,2) DEFAULT 0.5,
            skill_level ENUM('beginner', 'intermediate', 'advanced', 'expert') DEFAULT 'intermediate',
            prep_complexity INT DEFAULT 5,
            cooking_complexity INT DEFAULT 5,
            technique_count INT DEFAULT 0,
            equipment_required TEXT,
            techniques_required TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_recipe (recipe_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_cooking_skills (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            skill_level ENUM('beginner', 'intermediate', 'advanced', 'expert') DEFAULT 'beginner',
            techniques_mastered TEXT,
            equipment_owned TEXT,
            dietary_restrictions TEXT,
            preferences TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_skills (user_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("   ✓ recipe_difficulty and user_cooking_skills created")
    
    # 4. Wine Pairings
    print("\n4. Creating wine_pairings table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wine_pairings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            recipe_id INT NOT NULL,
            wine_type VARCHAR(100) NOT NULL,
            wine_variety VARCHAR(100),
            pairing_score DECIMAL(3,2) DEFAULT 0.8,
            reasoning TEXT,
            price_range ENUM('budget', 'mid-range', 'premium', 'luxury') DEFAULT 'mid-range',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_recipe_wine (recipe_id),
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)
    print("   ✓ wine_pairings created")
    
    # 5. Grocery List Categories
    print("\n5. Creating grocery_categories table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grocery_categories (
            id INT PRIMARY KEY AUTO_INCREMENT,
            category_name VARCHAR(100) NOT NULL,
            store_section VARCHAR(100),
            aisle_number INT,
            display_order INT DEFAULT 0,
            icon VARCHAR(50),
            UNIQUE KEY unique_category (category_name)
        )
    """)
    
    # Insert default categories
    cursor.execute("""
        INSERT IGNORE INTO grocery_categories (category_name, store_section, display_order, icon) VALUES
        ('Produce', 'Fresh Section', 1, '🥬'),
        ('Meat & Seafood', 'Refrigerated', 2, '🥩'),
        ('Dairy & Eggs', 'Refrigerated', 3, '🥛'),
        ('Bakery', 'Fresh Section', 4, '🍞'),
        ('Pantry Staples', 'Center Aisles', 5, '🥫'),
        ('Spices & Seasonings', 'Center Aisles', 6, '🌶️'),
        ('Grains & Pasta', 'Center Aisles', 7, '🍚'),
        ('Canned Goods', 'Center Aisles', 8, '🥫'),
        ('Frozen Foods', 'Frozen Section', 9, '🧊'),
        ('Beverages', 'Center Aisles', 10, '🥤'),
        ('Snacks', 'Center Aisles', 11, '🍿'),
        ('Condiments', 'Center Aisles', 12, '🍯'),
        ('Other', 'Misc', 99, '📦')
    """)
    print("   ✓ grocery_categories created with default data")
    
    # 6. Cooking Sessions (for AI Coach)
    print("\n6. Creating cooking_sessions table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cooking_sessions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            recipe_id INT NOT NULL,
            session_status ENUM('not_started', 'in_progress', 'paused', 'completed', 'abandoned') DEFAULT 'not_started',
            current_step INT DEFAULT 0,
            total_steps INT,
            start_time TIMESTAMP NULL,
            end_time TIMESTAMP NULL,
            total_duration INT,
            voice_enabled BOOLEAN DEFAULT FALSE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_sessions (user_id),
            INDEX idx_active_sessions (session_status, user_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
        )
    """)
    print("   ✓ cooking_sessions created")
    
    # 7. Leftover Tracker
    print("\n7. Creating leftovers table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leftovers (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            original_recipe_id INT,
            leftover_name VARCHAR(255) NOT NULL,
            quantity DECIMAL(10,2),
            unit VARCHAR(50),
            storage_date DATE NOT NULL,
            expiry_date DATE,
            location VARCHAR(100) DEFAULT 'fridge',
            ingredients TEXT,
            notes TEXT,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_leftovers (user_id),
            INDEX idx_unused (used, user_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (original_recipe_id) REFERENCES recipes(id) ON DELETE SET NULL
        )
    """)
    print("   ✓ leftovers created")
    
    conn.commit()
    
    print("\n" + "=" * 70)
    print("✓ All tables created successfully!")
    print("=" * 70)
    print("\nFeatures Ready:")
    print("  1. ✓ Ingredient Expiry Tracker")
    print("  2. ✓ Nutrition Goals Tracker")
    print("  3. ✓ Recipe Difficulty Predictor")
    print("  4. ✓ Wine Pairing Suggestions")
    print("  5. ✓ Smart Grocery List")
    print("  6. ✓ AI Cooking Coach")
    print("  7. ✓ Leftover Transformer")
    print("  8. ✓ Recipe Scaling (no table needed)")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
