from dotenv import load_dotenv; load_dotenv()
from database import Database
import time

db = Database()
tag_ids = [1, 2, 3, 4, 5]
loved_ids = [1, 2, 3]
ph_tags = ','.join(['%s'] * len(tag_ids))
ph_loved = ','.join(['%s'] * len(loved_ids))

# OLD query (33 seconds)
t1 = time.time()
q_old = f"""SELECT r.id, r.name, r.minutes, r.image_url, n.calories,
       COUNT(DISTINCT rt.tag_id) AS tag_match
FROM recipes r
LEFT JOIN nutrition n ON r.id = n.recipe_id
JOIN recipe_tags rt ON r.id = rt.recipe_id
WHERE rt.tag_id IN ({ph_tags})
  AND r.id NOT IN ({ph_loved})
GROUP BY r.id
ORDER BY tag_match DESC
LIMIT 6"""
result_old = db.execute_query(q_old, tuple(tag_ids) + tuple(loved_ids), fetch=True)
t2 = time.time()
print(f"OLD query: {t2-t1:.2f}s  results={len(result_old or [])}")

# NEW query (subquery approach)
t3 = time.time()
q_new = f"""SELECT r.id, r.name, r.minutes, r.image_url, n.calories, top.tag_match
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
LEFT JOIN nutrition n ON r.id = n.recipe_id
ORDER BY top.tag_match DESC
LIMIT 6"""
result_new = db.execute_query(q_new, tuple(tag_ids) + tuple(loved_ids), fetch=True)
t4 = time.time()
print(f"NEW query: {t4-t3:.2f}s  results={len(result_new or [])}")

if result_new:
    for r in result_new[:3]:
        print(f"  {r['name']}  tag_match={r['tag_match']}")

print(f"\nSpeedup: {(t2-t1)/(t4-t3):.1f}x faster")
