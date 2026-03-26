"""
Pre-fetch Unsplash images for recipes that still have broken URLs.
Runs in the background, respects Unsplash rate limits.

Usage:
    python prefetch_images.py                   # Run once (single batch then stop)
    python prefetch_images.py --continuous       # Run 24/7, free tier (45/hr)
    python prefetch_images.py --continuous --production  # Run 24/7, production (4500/hr)
"""
import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

from database import Database

# ── Config ──────────────────────────────────────────────────────────
IS_PRODUCTION = '--production' in sys.argv
BATCH_SIZE    = 4500 if IS_PRODUCTION else 45   # production: 5000/hr, keep 500 buffer
DELAY_BETWEEN = 0.5 if IS_PRODUCTION else 2     # faster in production
HOUR_SLEEP    = 3660                             # wait ~61 min between batches

db = Database()
UNSPLASH_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

if not UNSPLASH_KEY or UNSPLASH_KEY == 'your-access-key-here':
    print("ERROR: Set UNSPLASH_ACCESS_KEY in backend/.env first")
    sys.exit(1)


def get_broken_recipes(limit):
    """Get recipes that still have broken source.unsplash.com URLs"""
    return db.execute_query(
        "SELECT id, name FROM recipes "
        "WHERE image_url LIKE %s "
        "ORDER BY id ASC LIMIT %s",
        ('%source.unsplash.com%', limit), fetch=True
    )


def fetch_image(recipe_id, recipe_name):
    """Fetch a real image from Unsplash and save to DB"""
    try:
        query = recipe_name + ' food dish'
        resp = requests.get('https://api.unsplash.com/search/photos', params={
            'query': query,
            'per_page': 1,
            'orientation': 'landscape',
            'content_filter': 'high'
        }, headers={'Authorization': f'Client-ID {UNSPLASH_KEY}'}, timeout=10)

        if resp.status_code == 403:
            print(f"\n  RATE LIMITED by Unsplash! Waiting 1 hour...")
            return 'rate_limited'

        if resp.status_code == 200 and resp.json().get('results'):
            img = resp.json()['results'][0]
            image_url = img['urls'].get('small', img['urls']['regular'])

            db.execute_query(
                "UPDATE recipes SET image_url = %s WHERE id = %s",
                (image_url, recipe_id)
            )
            return 'ok'
        else:
            # No results — mark as empty so we skip next time
            db.execute_query(
                "UPDATE recipes SET image_url = '' WHERE id = %s",
                (recipe_id,)
            )
            return 'no_result'

    except requests.RequestException as e:
        print(f"\n  Network error: {e}")
        return 'error'


def run_batch():
    """Fetch one batch of images"""
    recipes = get_broken_recipes(BATCH_SIZE)
    if not recipes:
        print("All recipes have real images! Nothing to do.")
        return 0

    fetched = 0
    skipped = 0
    for i, recipe in enumerate(recipes, 1):
        result = fetch_image(recipe['id'], recipe['name'])

        if result == 'rate_limited':
            print(f"  Got {fetched} images before rate limit hit.")
            return fetched

        if result == 'ok':
            fetched += 1
            sys.stdout.write(f"\r  [{i}/{len(recipes)}] Cached: {fetched} | {recipe['name'][:40]}...   ")
        else:
            skipped += 1
            sys.stdout.write(f"\r  [{i}/{len(recipes)}] Skipped: {skipped} | {recipe['name'][:40]}...   ")

        sys.stdout.flush()
        time.sleep(DELAY_BETWEEN)

    print(f"\n  Batch done: {fetched} cached, {skipped} skipped")
    return fetched


def count_remaining():
    """Count how many recipes still need images"""
    result = db.execute_query(
        "SELECT COUNT(*) as c FROM recipes WHERE image_url LIKE %s",
        ('%source.unsplash.com%',), fetch=True
    )
    return result[0]['c'] if result else 0


def count_cached():
    """Count recipes with real images"""
    result = db.execute_query(
        "SELECT COUNT(*) as c FROM recipes "
        "WHERE image_url IS NOT NULL AND image_url != '' "
        "AND image_url NOT LIKE %s",
        ('%source.unsplash.com%',), fetch=True
    )
    return result[0]['c'] if result else 0


def main():
    continuous = '--continuous' in sys.argv

    print("=" * 55)
    print("  Unsplash Image Pre-Fetcher")
    print("=" * 55)
    print(f"  Mode: {'Continuous (24/7)' if continuous else 'Single batch'}" +
          (f" [PRODUCTION - {BATCH_SIZE}/hr]" if IS_PRODUCTION else f" [Free tier - {BATCH_SIZE}/hr]"))
    print(f"  Rate: {BATCH_SIZE} images/hour")
    print(f"  Remaining: {count_remaining():,} recipes need images")
    print(f"  Already cached: {count_cached():,} recipes have real images")
    print("=" * 55)

    total_fetched = 0
    batch_num = 0

    while True:
        batch_num += 1
        remaining = count_remaining()

        if remaining == 0:
            print("\nAll done! Every recipe has a real image.")
            break

        print(f"\n--- Batch #{batch_num} | {remaining:,} remaining ---")
        fetched = run_batch()
        total_fetched += fetched

        if not continuous:
            print(f"\nTotal cached this run: {total_fetched}")
            print(f"Remaining: {count_remaining():,}")
            print(f"\nRun with --continuous to keep going (45 images/hour)")
            break

        # Wait for rate limit to reset
        print(f"\n  Total so far: {total_fetched:,} | Sleeping {HOUR_SLEEP//60} min until next batch...")
        time.sleep(HOUR_SLEEP)


if __name__ == '__main__':
    main()
