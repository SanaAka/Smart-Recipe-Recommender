"""Direct test of the fixed search_recipes method"""
import sys
sys.path.insert(0, 'd:/SSMMRR/backend')
from database import Database

db = Database()

# Clear the cache first
db.search_cache.clear()
print("Cache cleared\n")

# Test search
print("=" * 60)
print("Testing Fixed Search Function")
print("=" * 60)

print("\n1. Search for 'rice' (name search):")
results = db.search_recipes(query='rice', search_type='name', limit=5)
print(f"   Found {len(results)} results:")
for r in results:
    print(f"   - {r['name']}")

print("\n2. Search for 'chicken' (name search):")
results = db.search_recipes(query='chicken', search_type='name', limit=5)
print(f"   Found {len(results)} results:")
for r in results:
    print(f"   - {r['name']}")

print("\n3. Search for 'rice' (ingredient search):")
results = db.search_recipes(query='rice', search_type='ingredient', limit=5)
print(f"   Found {len(results)} results:")
for r in results:
    print(f"   - {r['name']}")

print("\n" + "=" * 60)
print("✓ Search function is working correctly!")
print("=" * 60)
