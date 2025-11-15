"""Check database state and import data if needed"""
import os
from dotenv import load_dotenv
from database import Database
from data_preprocessor import DataPreprocessor

# Load environment variables
load_dotenv()

def main():
    print("=" * 60)
    print("Checking Database State")
    print("=" * 60)
    
    # Initialize database
    db = Database()
    
    try:
        # Get current stats
        stats = db.get_stats()
        print(f"\n✓ Database connected successfully!")
        print(f"  - Total recipes: {stats['total_recipes']}")
        print(f"  - Total ingredients: {stats['total_ingredients']}")
        print(f"  - Total tags: {stats['total_tags']}")
        
        if stats['total_recipes'] == 0:
            print("\n⚠ No recipes found in database!")
            print("Starting data import process...\n")
            
            # Import data
            csv_file = 'data/recipes_data.csv'
            if not os.path.exists(csv_file):
                print(f"✗ Error: {csv_file} not found!")
                return
            
            preprocessor = DataPreprocessor(db)
            preprocessor.load_data_from_csv(csv_file, limit=5000)
            
            # Get updated stats
            stats = db.get_stats()
            print(f"\n✓ Data import completed!")
            print(f"  - Total recipes: {stats['total_recipes']}")
            print(f"  - Total ingredients: {stats['total_ingredients']}")
            print(f"  - Total tags: {stats['total_tags']}")
        else:
            print(f"\n✓ Database already populated with {stats['total_recipes']} recipes")
            
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    main()
