import mysql.connector, os
from dotenv import load_dotenv
load_dotenv('d:/SSMMRR/backend/.env')
c = mysql.connector.connect(host='127.0.0.1', user='root', password=os.getenv('DB_PASSWORD'), database='recipe_recommender')
cur = c.cursor(dictionary=True)
cur.execute('SELECT id, name, search_text, submitted_by FROM recipes ORDER BY id DESC LIMIT 5')
for r in cur.fetchall():
    print(f"id={r['id']}  name={r['name']!r}  search_text={r['search_text']!r}  submitted_by={r['submitted_by']}")
cur.close()
c.close()
