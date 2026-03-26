from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

from database import Database
db = Database()
db.connect()

# Check what image_url looks like in the DB
rows = db.execute_query("""
    SELECT id, name, image_url 
    FROM recipes 
    ORDER BY RAND() 
    LIMIT 10
""", fetch=True)

for r in rows:
    url = r.get('image_url') or 'NULL'
    name = r['name'][:30].ljust(30)
    print(f"ID {r['id']}: {name} | {url[:80]}")

# Count stats
stats = db.execute_query("""
    SELECT 
        COUNT(*) as total,
        SUM(image_url IS NOT NULL AND image_url != '') as has_url,
        SUM(image_url IS NULL OR image_url = '') as no_url
    FROM recipes
""", fetch=True)
print()
s = stats[0]
print(f"Total: {s['total']} | With URL: {s['has_url']} | No URL: {s['no_url']}")
db.disconnect()
