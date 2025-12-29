from database import Database

db = Database()

# Test ingredient search
print("Testing ingredient search...")
print("\n1. Searching for 'chicken':")
results = db.search_recipes('chicken', search_type='ingredient', limit=10)
print(f"   Found {len(results)} recipes")
if results:
    for i, r in enumerate(results[:5], 1):
        print(f"   {i}. {r['name']}")
        if r.get('ingredients'):
            ings = r['ingredients'][:3] if isinstance(r['ingredients'], list) else r['ingredients'].split('|')[:3]
            print(f"      Ingredients: {', '.join(ings)}...")
else:
    print("   No results found")

print("\n2. Searching for 'salt':")
results = db.search_recipes('salt', search_type='ingredient', limit=5)
print(f"   Found {len(results)} recipes")
if results:
    for i, r in enumerate(results[:3], 1):
        print(f"   {i}. {r['name']}")

print("\n3. Searching for 'tomato':")
results = db.search_recipes('tomato', search_type='ingredient', limit=5)
print(f"   Found {len(results)} recipes")
if results:
    for i, r in enumerate(results[:3], 1):
        print(f"   {i}. {r['name']}")

# Check if ingredients table has data
print("\n4. Checking ingredients table:")
result = db.execute_query("SELECT COUNT(*) as cnt FROM ingredients", fetch=True)
print(f"   Total ingredients in DB: {result[0]['cnt'] if result else 0}")

result = db.execute_query("SELECT name FROM ingredients LIMIT 10", fetch=True)
if result:
    print(f"   Sample ingredients: {', '.join([r['name'] for r in result[:10]])}")
