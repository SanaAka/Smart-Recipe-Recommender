"""Clear database and reimport recipes with higher limit"""
import os
from dotenv import load_dotenv
from database import Database
from data_preprocessor import DataPreprocessor

# Load environment variables
load_dotenv()

def main():
    print("=" * 60)
    print("Reimporting Recipe Data")
    print("=" * 60)
    
    db = Database()
    
    try:
        # Clear existing data
        print("\n1. Clearing existing data...")
        db.execute_query("SET FOREIGN_KEY_CHECKS = 0")
        
        tables = ['recipe_ingredients', 'recipe_tags', 'steps', 'nutrition', 'recipes', 'ingredients', 'tags']
        for table in tables:
            print(f"   Clearing {table}...")
            db.execute_query(f"TRUNCATE TABLE {table}")
        
        db.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        print("   ✓ Database cleared")
        
        # Import new data
        print("\n2. Importing 2,000,000 recipes...")
        
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file = os.path.join(script_dir, 'data', 'recipes_data.csv')
        
        if not os.path.exists(csv_file):
            print(f"✗ Error: {csv_file} not found!")
            return
        
        preprocessor = DataPreprocessor()
        preprocessor.process_and_load(csv_file, limit=2000000)
        
        # Get final stats
        print("\n3. Verifying import...")
        stats = db.get_stats()
        print(f"\n✓ Import completed successfully!")
        print(f"  - Total recipes: {stats['total_recipes']:,}")
        print(f"  - Total ingredients: {stats['total_ingredients']:,}")
        print(f"  - Total tags: {stats['total_tags']:,}")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()
    
    print("\n" + "=" * 60)
    print("Next: Restart the backend server to retrain the ML model")
    print("=" * 60)

if __name__ == '__main__':
    main()
