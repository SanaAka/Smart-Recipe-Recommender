"""Check search_text column status"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor(dictionary=True)

# Check total recipes
cursor.execute('SELECT COUNT(*) as total FROM recipes')
total = cursor.fetchone()['total']
print(f'Total recipes: {total}')

# Check empty search_text
cursor.execute('SELECT COUNT(*) as total FROM recipes WHERE search_text IS NULL OR search_text = ""')
empty = cursor.fetchone()['total']
print(f'Empty search_text: {empty}')

# Check filled search_text
cursor.execute('SELECT COUNT(*) as total FROM recipes WHERE search_text IS NOT NULL AND search_text != ""')
filled = cursor.fetchone()['total']
print(f'Filled search_text: {filled}')

# Sample recipes
cursor.execute('SELECT id, name, SUBSTRING(search_text, 1, 100) as text_preview FROM recipes LIMIT 5')
rows = cursor.fetchall()
print('\nSample recipes:')
for r in rows:
    print(f'{r["id"]}: {r["name"][:50]} -> search_text: {r["text_preview"]}')

# Test fulltext search
print('\n--- Testing FULLTEXT search ---')
cursor.execute('SELECT id, name FROM recipes WHERE MATCH(search_text) AGAINST("+rice" IN BOOLEAN MODE) LIMIT 5')
fulltext_results = cursor.fetchall()
print(f'Fulltext search results for "rice": {len(fulltext_results)}')
for r in fulltext_results:
    print(f'  - {r["name"]}')

# Test LIKE search fallback
print('\n--- Testing LIKE search fallback ---')
cursor.execute('SELECT id, name FROM recipes WHERE name LIKE %s LIMIT 5', ('%rice%',))
like_results = cursor.fetchall()
print(f'LIKE search results for "rice": {len(like_results)}')
for r in like_results:
    print(f'  - {r["name"]}')

cursor.close()
conn.close()
