"""
Data Preprocessor for Recipe Dataset
Processes the Kaggle Recipe Dataset and loads it into MySQL database
"""

import pandas as pd
import json
import ast
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

class DataPreprocessor:
    def __init__(self):
        self.connection = None
        self.ingredient_cache = {}  # Cache for ingredient IDs
        self.tag_cache = {}  # Cache for tag IDs
        self.connect_db()

    def connect_db(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'recipe_recommender')
            )
            print("Successfully connected to database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            raise

    def safe_eval(self, val):
        """Safely evaluate string representation of lists"""
        if pd.isna(val):
            return []
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                return ast.literal_eval(val)
            except:
                return []
        return []

    def load_csv_data(self, csv_path, limit=10000):
        """Load and preprocess CSV data"""
        print(f"Loading data from {csv_path}...")
        
        # Read CSV file
        df = pd.read_csv(csv_path, nrows=limit)
        print(f"Loaded {len(df)} recipes")
        
        # Map column names to our expected format
        # This dataset has: title, ingredients, directions, link, source, NER, site
        df = df.rename(columns={
            'title': 'name',
            'directions': 'steps'
        })
        
        # Add default values for missing columns
        df['minutes'] = 30  # Default cooking time
        df['description'] = df['name']  # Use name as description
        df['tags'] = df.get('NER', '[]')  # Use NER (Named Entity Recognition) as tags
        df['nutrition'] = '[]'  # No nutrition data in this dataset
        
        # Clean and process data
        df['name'] = df['name'].fillna('Unknown Recipe')
        
        # Process list columns
        df['ingredients'] = df['ingredients'].apply(self.safe_eval)
        df['tags'] = df['tags'].apply(self.safe_eval)
        df['steps'] = df['steps'].apply(self.safe_eval)
        
        # Filter out recipes with no ingredients
        df = df[df['ingredients'].apply(len) > 0]
        
        print(f"After cleaning: {len(df)} recipes")
        return df

    def insert_recipe(self, row):
        """Insert a recipe into the database"""
        cursor = self.connection.cursor()
        
        try:
            # Insert recipe
            recipe_query = """
                INSERT INTO recipes (name, minutes, description)
                VALUES (%s, %s, %s)
            """
            
            # Handle description - convert float/NaN to None
            description = row.get('description')
            if description and isinstance(description, str):
                description = description[:5000]
            else:
                description = None
            
            cursor.execute(recipe_query, (
                row['name'][:500],
                int(row.get('minutes', 30)),
                description
            ))
            recipe_id = cursor.lastrowid

            # Batch insert ingredients
            if row['ingredients']:
                ingredient_ids = []
                for ingredient_name in row['ingredients']:
                    if not ingredient_name or len(ingredient_name) > 255:
                        continue
                    
                    ingredient_name = ingredient_name.lower().strip()
                    
                    # Check cache first
                    if ingredient_name not in self.ingredient_cache:
                        cursor.execute(
                            "SELECT id FROM ingredients WHERE name = %s",
                            (ingredient_name,)
                        )
                        result = cursor.fetchone()
                        
                        if result:
                            self.ingredient_cache[ingredient_name] = result[0]
                        else:
                            cursor.execute(
                                "INSERT INTO ingredients (name) VALUES (%s)",
                                (ingredient_name,)
                            )
                            self.ingredient_cache[ingredient_name] = cursor.lastrowid
                    
                    ingredient_ids.append(self.ingredient_cache[ingredient_name])
                
                # Batch insert recipe-ingredient relationships
                if ingredient_ids:
                    cursor.executemany(
                        "INSERT IGNORE INTO recipe_ingredients (recipe_id, ingredient_id) VALUES (%s, %s)",
                        [(recipe_id, iid) for iid in ingredient_ids]
                    )

            # Batch insert tags
            if row['tags']:
                tag_ids = []
                for tag_name in row['tags']:
                    if not tag_name or len(tag_name) > 255:
                        continue
                    
                    tag_name = tag_name.lower().strip()
                    
                    # Check cache first
                    if tag_name not in self.tag_cache:
                        cursor.execute(
                            "SELECT id FROM tags WHERE name = %s",
                            (tag_name,)
                        )
                        result = cursor.fetchone()
                        
                        if result:
                            self.tag_cache[tag_name] = result[0]
                        else:
                            cursor.execute(
                                "INSERT INTO tags (name) VALUES (%s)",
                                (tag_name,)
                            )
                            self.tag_cache[tag_name] = cursor.lastrowid
                    
                    tag_ids.append(self.tag_cache[tag_name])
                
                # Batch insert recipe-tag relationships
                if tag_ids:
                    cursor.executemany(
                        "INSERT IGNORE INTO recipe_tags (recipe_id, tag_id) VALUES (%s, %s)",
                        [(recipe_id, tid) for tid in tag_ids]
                    )

            # Insert steps (batch)
            if row['steps']:
                steps_data = []
                for idx, step in enumerate(row['steps'], 1):
                    if not step:
                        continue
                    steps_data.append((recipe_id, idx, step[:5000]))
                
                if steps_data:
                    cursor.executemany(
                        "INSERT INTO steps (recipe_id, step_number, description) VALUES (%s, %s, %s)",
                        steps_data
                    )

            return recipe_id

        except Error as e:
            print(f"Error inserting recipe '{row.get('name', 'Unknown')}': {e}")
            return None
        finally:
            cursor.close()

    def process_and_load(self, csv_path, limit=10000):
        """Process CSV and load into database"""
        df = self.load_csv_data(csv_path, limit)
        
        print("Inserting recipes into database...")
        print("This will take approximately 15-30 minutes for 2M recipes...")
        success_count = 0
        
        # Commit every N recipes for better performance
        commit_batch = 1000
        
        for idx, row in df.iterrows():
            if idx % 5000 == 0:
                print(f"Processed {idx:,}/{len(df):,} recipes...")
            
            recipe_id = self.insert_recipe(row)
            if recipe_id:
                success_count += 1
            
            # Commit in batches for better performance
            if (idx + 1) % commit_batch == 0:
                self.connection.commit()
        
        # Final commit
        self.connection.commit()
        print(f"\n✓ Successfully inserted {success_count:,} recipes into database")
        
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")


if __name__ == '__main__':
    # Update this path to your downloaded Kaggle dataset CSV file
    CSV_FILE = 'data/recipes_data.csv'
    
    if not os.path.exists(CSV_FILE):
        print(f"Error: CSV file not found at {CSV_FILE}")
        print("Please download the dataset from Kaggle and update the CSV_FILE path")
        exit(1)
    
    preprocessor = DataPreprocessor()
    
    try:
        # Process and load data (adjust limit as needed)
        preprocessor.process_and_load(CSV_FILE, limit=5000)
    except Exception as e:
        print(f"Error during processing: {e}")
    finally:
        preprocessor.close()
