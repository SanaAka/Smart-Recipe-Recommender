import sys, os, time
sys.path.insert(0, r'D:\SSMMRR\backend')
os.chdir(r'D:\SSMMRR\backend')
from dotenv import load_dotenv; load_dotenv(r'D:\SSMMRR\backend\.env')
from database import Database
db = Database()

tag_ids = [1, 2, 3, 4, 5]
loved_ids = [1, 2, 3]
ph_t = ','.join(['%s'] * len(tag_ids))
ph_l = ','.join(['%s'] * len(loved_ids))

t1 = time.time()
r = db.execute_query(f"""
SELECT rt.recipe_id, COUNT(DISTINCT rt.tag_id) AS tag_match
FROM recipe_tags rt
WHERE rt.tag_id IN ({ph_t}) AND rt.recipe_id NOT IN ({ph_l})
GROUP BY rt.recipe_id ORDER BY tag_match DESC LIMIT 50
""", tuple(tag_ids) + tuple(loved_ids), fetch=True)
t2 = time.time()

with open(r'D:\SSMMRR\_result.txt', 'w') as f:
    f.write(f"Subquery: {t2-t1:.2f}s rows={len(r or [])}\n")
    if r:
        for x in r[:3]:
            f.write(f"  recipe_id={x['recipe_id']} tags={x['tag_match']}\n")
print(f"Done: {t2-t1:.2f}s")
