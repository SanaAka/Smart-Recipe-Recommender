"""
Database Setup Script
Run this to create the database and tables
"""

import mysql.connector
from mysql.connector import Error
import getpass
import os

def create_database_and_tables():
    """Create database and all tables"""
    
    print("=" * 50)
    print("Smart Recipe Recommender - Database Setup")
    print("=" * 50)
    print()
    
    # Get MySQL credentials
    host = input("Enter MySQL host (default: localhost): ").strip() or "localhost"
    user = input("Enter MySQL username (default: root): ").strip() or "root"
    password = getpass.getpass("Enter MySQL password: ")
    
    connection = None
    try:
        # Connect to MySQL server (without database)
        print("\nConnecting to MySQL server...")
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        cursor = connection.cursor()
        
        # Create database
        print("Creating database 'recipe_recommender'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS recipe_recommender")
        cursor.execute("USE recipe_recommender")
        
        # Create tables
        print("Creating tables...")
        
        # Recipes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
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
        
        # Ingredients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Recipe-Ingredients relationship table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
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
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL UNIQUE,
                INDEX idx_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Recipe-Tags relationship table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_tags (
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
        
        # Nutrition table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nutrition (
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
        
        # Steps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS steps (
                id INT PRIMARY KEY AUTO_INCREMENT,
                recipe_id INT NOT NULL,
                step_number INT NOT NULL,
                description TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                INDEX idx_recipe (recipe_id),
                INDEX idx_step_number (step_number)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        connection.commit()
        
        print("\n✓ Database and tables created successfully!")
        print("\nDatabase: recipe_recommender")
        print("Tables: recipes, ingredients, tags, nutrition, steps, and junction tables")
        
        # Update .env file
        env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
        if os.path.exists(env_path):
            print(f"\nUpdating .env file at: {env_path}")
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Update database credentials
            env_content = env_content.replace('DB_PASSWORD=', f'DB_PASSWORD={password}')
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            print("✓ .env file updated")
        
        print("\nNext steps:")
        print("1. cd backend")
        print("2. python data_preprocessor.py")
        print("3. Wait for data to load (10-30 minutes)")
        print("4. python app.py")
        
    except Error as e:
        print(f"\n✗ Error: {e}")
        if str(e).startswith("1045"):
            print("\n💡 Tip: The MySQL password is incorrect.")
            print("   - If you haven't set a password, try pressing Enter for empty password")
            print("   - Check your MySQL installation for the correct password")
            print("   - On fresh installs, root password might be empty or 'root'")
        return False
        
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    
    return True

if __name__ == '__main__':
    create_database_and_tables()
