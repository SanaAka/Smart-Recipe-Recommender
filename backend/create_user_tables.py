"""Create user management tables for authentication system"""
import mysql.connector
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Read schema file
schema_file = Path(__file__).parent.parent / 'database' / 'user_management_schema.sql'
with open(schema_file, 'r', encoding='utf-8') as f:
    sql_commands = f.read()

# Connect and execute
connection = mysql.connector.connect(
    host='127.0.0.1',
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    database=os.getenv('DB_NAME', 'recipe_recommender')
)

cursor = connection.cursor()

# Split and execute each statement
statements = [s.strip() for s in sql_commands.split(';') if s.strip()]

print("Creating user management tables...")
for i, statement in enumerate(statements, 1):
    if statement:
        try:
            cursor.execute(statement)
            print(f"✓ Statement {i} executed successfully")
        except mysql.connector.Error as e:
            print(f"✗ Statement {i} failed: {e}")

connection.commit()
cursor.close()
connection.close()

print("\n✓ User management schema created successfully!")
print("Tables: users, user_favorites, recipe_ratings, user_cooking_history, user_recipe_views")
