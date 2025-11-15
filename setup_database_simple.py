# Simple Database Setup - No Password Prompt
# Use this if you know your MySQL credentials

import mysql.connector
from mysql.connector import Error

# ==========================================
# CONFIGURE YOUR MYSQL CREDENTIALS HERE:
# ==========================================
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "0965256310Kh@"  # <-- PUT YOUR PASSWORD HERE (or leave empty if no password)
# ==========================================

def setup_database():
    """Create database and tables"""
    
    print("=" * 60)
    print("Setting up Recipe Recommender Database...")
    print("=" * 60)
    
    connection = None
    try:
        # Connect to MySQL
        print(f"\nConnecting to MySQL at {MYSQL_HOST} as {MYSQL_USER}...")
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        
        cursor = connection.cursor()
        print("✓ Connected successfully!")
        
        # Create database
        print("\nCreating database 'recipe_recommender'...")
        cursor.execute("DROP DATABASE IF EXISTS recipe_recommender")
        cursor.execute("CREATE DATABASE recipe_recommender")
        cursor.execute("USE recipe_recommender")
        print("✓ Database created!")
        
        # Create tables
        print("\nCreating tables...")
        
        # Recipes
        cursor.execute("""
            CREATE TABLE recipes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(500) NOT NULL,
                minutes INT,
                description TEXT,
                contributor_id INT,
                submitted DATE,
                INDEX idx_name (name(255)),
                INDEX idx_minutes (minutes)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ recipes")
        
        # Ingredients
        cursor.execute("""
            CREATE TABLE ingredients (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ ingredients")
        
        # Recipe-Ingredients
        cursor.execute("""
            CREATE TABLE recipe_ingredients (
                id INT PRIMARY KEY AUTO_INCREMENT,
                recipe_id INT NOT NULL,
                ingredient_id INT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
                UNIQUE KEY unique_recipe_ingredient (recipe_id, ingredient_id),
                INDEX idx_recipe (recipe_id),
                INDEX idx_ingredient (ingredient_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ recipe_ingredients")
        
        # Tags
        cursor.execute("""
            CREATE TABLE tags (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ tags")
        
        # Recipe-Tags
        cursor.execute("""
            CREATE TABLE recipe_tags (
                id INT PRIMARY KEY AUTO_INCREMENT,
                recipe_id INT NOT NULL,
                tag_id INT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                UNIQUE KEY unique_recipe_tag (recipe_id, tag_id),
                INDEX idx_recipe (recipe_id),
                INDEX idx_tag (tag_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ recipe_tags")
        
        # Nutrition
        cursor.execute("""
            CREATE TABLE nutrition (
                id INT PRIMARY KEY AUTO_INCREMENT,
                recipe_id INT NOT NULL UNIQUE,
                calories DECIMAL(10, 2),
                total_fat DECIMAL(10, 2),
                sugar DECIMAL(10, 2),
                sodium DECIMAL(10, 2),
                protein DECIMAL(10, 2),
                saturated_fat DECIMAL(10, 2),
                carbohydrates DECIMAL(10, 2),
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                INDEX idx_recipe (recipe_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ nutrition")
        
        # Steps
        cursor.execute("""
            CREATE TABLE steps (
                id INT PRIMARY KEY AUTO_INCREMENT,
                recipe_id INT NOT NULL,
                step_number INT NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                INDEX idx_recipe (recipe_id),
                INDEX idx_step_number (step_number)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("  ✓ steps")
        
        connection.commit()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print(f"\nDatabase Name: recipe_recommender")
        print(f"Tables Created: 7 tables")
        print(f"\nNext Step: Load recipe data")
        print(f"  cd backend")
        print(f"  python data_preprocessor.py")
        
        cursor.close()
        return True
        
    except Error as e:
        print(f"\n❌ MySQL Error: {e}")
        
        if "1045" in str(e):
            print("\n💡 Authentication Failed!")
            print("   1. Open this file: setup_database_simple.py")
            print("   2. Edit line 8-10 with your MySQL credentials")
            print("   3. Save and run again")
        elif "2003" in str(e):
            print("\n💡 Cannot Connect to MySQL!")
            print("   1. Make sure MySQL is running")
            print("   2. Check Windows Services for 'MySQL' or 'MySQL80'")
            print("   3. Or run: net start MySQL80")
        
        return False
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\n✓ Connection closed")

if __name__ == '__main__':
    success = setup_database()
    
    if not success:
        print("\n" + "=" * 60)
        print("❌ Setup failed. Please fix the errors above and try again.")
        print("=" * 60)
        exit(1)
