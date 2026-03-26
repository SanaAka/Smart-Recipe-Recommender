import sys, time
from dotenv import load_dotenv; load_dotenv()
from database import Database
db = Database()

tag_ids = [1, 2, 3, 4, 5]
loved_ids = [1, 2, 3]
ph_tags = ','.join(['%s'] * len(tag_ids))
ph_loved = ','.join(['%s'] * len(loved_ids))

# NEW optimized query only
t1 = time.time()
q = f"""SELECT r.id, r.name, top.tag_match
FROM (
    SELECT rt.recipe_id, COUNT(DISTINCT rt.tag_id) AS tag_match
    FROM recipe_tags rt
    WHERE rt.tag_id IN ({ph_tags})
      AND rt.recipe_id NOT IN ({ph_loved})
    GROUP BY rt.recipe_id
    ORDER BY tag_match DESC
    LIMIT 50
) top
JOIN recipes r ON r.id = top.recipe_id
ORDER BY top.tag_match DESC
LIMIT 6"""
result = db.execute_query(q, tuple(tag_ids) + tuple(loved_ids), fetch=True)
t2 = time.time()

with open('_bench_out.txt', 'w') as f:
    f.write(f"NEW query: {t2-t1:.2f}s  results={len(result or [])}\n")
    if result:
        for r in result[:3]:
            f.write(f"  {r['name']}  tag_match={r['tag_match']}\n")

print(f"NEW query: {t2-t1:.2f}s  results={len(result or [])}")
