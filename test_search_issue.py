"""Test search functionality to debug rice query issue"""
import sys
sys.path.insert(0, 'd:/SSMMRR/backend')
from database import Database

db = Database()

print("=" * 60)
print("Testing Recipe Search Issue")
print("=" * 60)

# Test 1: Check total recipes
results = db.execute_query('SELECT COUNT(*) as total FROM recipes', fetch=True)
total_recipes = results[0]['total'] if results else 0
print(f"\n1. Total recipes in database: {total_recipes}")

# Test 2: Check recipes with 'rice' in name
results = db.execute_query('SELECT COUNT(*) as total FROM recipes WHERE name LIKE %s', ('%rice%',), fetch=True)
rice_count = results[0]['total'] if results else 0
print(f"2. Recipes with 'rice' in name: {rice_count}")

# Test 3: Sample rice recipes
if rice_count > 0:
    results = db.execute_query('SELECT name FROM recipes WHERE name LIKE %s LIMIT 5', ('%rice%',), fetch=True)
    print("\n3. Sample rice recipes:")
    for r in results:
        print(f"   - {r['name']}")

# Test 4: Check fulltext indexes
print("\n4. Checking fulltext indexes...")
results = db.execute_query("""
    SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
    AND INDEX_TYPE = 'FULLTEXT'
    ORDER BY TABLE_NAME, INDEX_NAME
""", fetch=True)

if results:
    print("   Found fulltext indexes:")
    for r in results:
        print(f"   - Table: {r['TABLE_NAME']}, Index: {r['INDEX_NAME']}, Column: {r['COLUMN_NAME']}")
else:
    print("   ⚠️  NO FULLTEXT INDEXES FOUND")

# Test 5: Check if search_text column exists
print("\n5. Checking for search_text column...")
has_search_text = db._has_column('recipes', 'search_text')
print(f"   search_text column exists: {has_search_text}")

# Test 6: Test the actual search_recipes method
print("\n6. Testing search_recipes() method...")
print("   Query: 'rice', Type: 'name'")
search_results = db.search_recipes(query='rice', search_type='name', limit=5)
print(f"   Results: {len(search_results)} recipes found")

if search_results:
    print("\n   Sample results:")
    for r in search_results:
        print(f"   - {r.get('name', 'Unknown')}")
else:
    print("   ⚠️  NO RESULTS RETURNED")

# Test 7: Test ingredient search
print("\n7. Testing ingredient search...")
print("   Query: 'rice', Type: 'ingredient'")
ingredient_results = db.search_recipes(query='rice', search_type='ingredient', limit=5)
print(f"   Results: {len(ingredient_results)} recipes found")

if ingredient_results:
    print("\n   Sample results:")
    for r in ingredient_results:
        print(f"   - {r.get('name', 'Unknown')}")
else:
    print("   ⚠️  NO RESULTS RETURNED")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
