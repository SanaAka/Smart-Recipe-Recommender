from dotenv import load_dotenv
load_dotenv()
from database import Database

db = Database()

total = db.execute_query('SELECT COUNT(*) as total FROM recipes', fetch=True)
print(f"Total recipes: {total[0]['total']:,}")

cached = db.execute_query(
    "SELECT COUNT(*) as c FROM recipes WHERE image_url IS NOT NULL "
    "AND image_url != '' "
    "AND image_url NOT LIKE '%source.unsplash%'",
    fetch=True
)
print(f"Already have real images: {cached[0]['c']:,}")
print(f"Still need images: {total[0]['total'] - cached[0]['c']:,}")
print(f"\nAt 45 images/hour, time to cache all: {(total[0]['total'] - cached[0]['c']) / 45:.0f} hours")
