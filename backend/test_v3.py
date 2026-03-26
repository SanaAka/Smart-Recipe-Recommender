"""
V3 Features - Software Testing Suite
Tests all V3 endpoints: auth, comment reactions, comment replies, user recipes
"""
import requests
import json
import time
import random
import string
import sys

BASE = "http://localhost:5000"
PASS = 0
FAIL = 0
ERRORS = []

def rand_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

def ok(name, resp, expected_status=200):
    global PASS, FAIL, ERRORS
    actual = resp.status_code
    if actual == expected_status:
        PASS += 1
        print(f"  [PASS] {name} (HTTP {actual})")
        return True
    else:
        FAIL += 1
        body = ""
        try: body = resp.json()
        except: body = resp.text[:200]
        ERRORS.append(f"{name}: expected {expected_status}, got {actual} => {body}")
        print(f"  [FAIL] {name} (expected {expected_status}, got {actual})")
        print(f"         Body: {body}")
        return False

def header(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# ============================================================================
print("=" * 70)
print("  SMART RECIPE RECOMMENDER V3 - TEST SUITE")
print("=" * 70)

# -- 1. HEALTH CHECK --
print("\n--- 1. Health Check ---")
r = requests.get(f"{BASE}/api/health")
ok("Health endpoint", r, 200)
data = r.json()
assert data["status"] == "healthy", "Not healthy!"
assert data["database"] == "connected", "DB not connected!"
print(f"     ML ready: {data.get('ml_ready')}")

# -- 2. AUTH: REGISTER --
print("\n--- 2. Auth: Register Test User ---")
test_user = f"testv3_{rand_str(6)}"
test_email = f"{test_user}@test.com"
test_pass = "TestPass123!"

r = requests.post(f"{BASE}/api/auth/register", json={
    "username": test_user,
    "email": test_email,
    "password": test_pass
})
if ok("Register new user", r, 201):
    data = r.json()
    TOKEN = data["access_token"]
    REFRESH = data.get("refresh_token", "")
    USER_ID = data["user"]["id"]
    print(f"     User: {test_user} (id={USER_ID})")
else:
    print("FATAL: Cannot register user, aborting tests")
    sys.exit(1)

# -- 3. AUTH: LOGIN --
print("\n--- 3. Auth: Login ---")
r = requests.post(f"{BASE}/api/auth/login", json={
    "username": test_user,
    "password": test_pass
})
ok("Login with correct creds", r, 200)

r = requests.post(f"{BASE}/api/auth/login", json={
    "username": test_user,
    "password": "WrongPass!"
})
ok("Login with wrong password (should 401)", r, 401)

# -- 4. AUTH: PROFILE --
print("\n--- 4. Auth: Profile ---")
r = requests.get(f"{BASE}/api/auth/profile", headers=header(TOKEN))
ok("Get profile (authenticated)", r, 200)

r = requests.get(f"{BASE}/api/auth/profile")
ok("Get profile (no token, should 401)", r, 401)

# -- 5. GET RECIPES (find a recipe to comment on) --
print("\n--- 5. Get a Recipe (for comment tests) ---")
r = requests.get(f"{BASE}/api/recipes", params={"page": 1, "limit": 1})
ok("Get recipes list", r, 200)
recipes = r.json().get("recipes", [])
if recipes:
    RECIPE_ID = recipes[0]["id"]
    print(f"     Using recipe id={RECIPE_ID}: {recipes[0].get('name','?')[:50]}")
else:
    print("FATAL: No recipes found, aborting")
    sys.exit(1)

# -- 6. COMMENTS CRUD --
print("\n--- 6. Comments CRUD ---")
# Post a comment
r = requests.post(f"{BASE}/api/recipe/{RECIPE_ID}/comments", 
    headers=header(TOKEN),
    json={"comment": f"Test comment by {test_user} - testing v3 features!"})
ok("Post new comment", r, 201)
if r.status_code == 201:
    COMMENT_ID = r.json().get("comment", {}).get("id")
    print(f"     Comment id={COMMENT_ID}")
else:
    # Try to get existing comments
    r2 = requests.get(f"{BASE}/api/recipe/{RECIPE_ID}/comments")
    comments = r2.json().get("comments", [])
    COMMENT_ID = comments[0]["id"] if comments else None
    print(f"     Using existing comment id={COMMENT_ID}")

# Get comments (should now include reaction fields)
r = requests.get(f"{BASE}/api/recipe/{RECIPE_ID}/comments")
ok("Get comments", r, 200)
if r.status_code == 200:
    comments = r.json().get("comments", [])
    if comments:
        c = comments[0]
        has_likes = "likes" in c
        has_dislikes = "dislikes" in c  
        has_reply_count = "reply_count" in c
        print(f"     Comments returned: {len(comments)}")
        print(f"     Has likes field: {has_likes}")
        print(f"     Has dislikes field: {has_dislikes}")
        print(f"     Has reply_count field: {has_reply_count}")
        if not (has_likes and has_dislikes and has_reply_count):
            FAIL += 1
            ERRORS.append("Comments missing v3 enrichment fields (likes/dislikes/reply_count)")
            print("  [FAIL] Missing v3 enrichment fields in comments!")
        else:
            PASS += 1
            print("  [PASS] Comments have v3 enrichment fields")

# -- 7. COMMENT REACTIONS --
print("\n--- 7. Comment Reactions ---")
if COMMENT_ID:
    # Like a comment
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/react",
        headers=header(TOKEN), json={"reaction": "like"})
    ok("Like a comment", r, 200)
    if r.status_code == 200:
        data = r.json()
        print(f"     Likes: {data.get('likes')}, Dislikes: {data.get('dislikes')}, User: {data.get('user_reaction')}")
        assert data.get("user_reaction") == "like", "user_reaction should be 'like'"

    # Like again (toggle off)
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/react",
        headers=header(TOKEN), json={"reaction": "like"})
    ok("Toggle like off", r, 200)
    if r.status_code == 200:
        data = r.json()
        print(f"     After toggle: Likes: {data.get('likes')}, User: {data.get('user_reaction')}")
        assert data.get("user_reaction") is None, "user_reaction should be None after toggle"

    # Dislike
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/react",
        headers=header(TOKEN), json={"reaction": "dislike"})
    ok("Dislike a comment", r, 200)
    if r.status_code == 200:
        data = r.json()
        print(f"     Dislikes: {data.get('dislikes')}, User: {data.get('user_reaction')}")

    # Switch to like (from dislike)
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/react",
        headers=header(TOKEN), json={"reaction": "like"})
    ok("Switch from dislike to like", r, 200)
    if r.status_code == 200:
        data = r.json()
        assert data.get("user_reaction") == "like"
        assert data.get("dislikes") == 0
        print(f"     After switch: Likes: {data.get('likes')}, Dislikes: {data.get('dislikes')}")

    # Invalid reaction
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/react",
        headers=header(TOKEN), json={"reaction": "love"})
    ok("Invalid reaction type (should 400)", r, 400)

    # No auth
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/react",
        json={"reaction": "like"})
    ok("React without auth (should 401)", r, 401)
else:
    print("  [SKIP] No comment to test reactions on")

# -- 8. COMMENT REPLIES --
print("\n--- 8. Comment Replies ---")
REPLY_ID = None
if COMMENT_ID:
    # Post a reply
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/replies",
        headers=header(TOKEN), json={"reply": "This is a test reply to the comment!"})
    ok("Post a reply", r, 201)
    if r.status_code == 201:
        reply_data = r.json().get("reply", {})
        REPLY_ID = reply_data.get("id")
        print(f"     Reply id={REPLY_ID}, text: {reply_data.get('reply','')[:50]}")

    # Post second reply
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/replies",
        headers=header(TOKEN), json={"reply": "Second test reply!"})
    ok("Post second reply", r, 201)

    # Get replies
    r = requests.get(f"{BASE}/api/comments/{COMMENT_ID}/replies")
    ok("Get replies for comment", r, 200)
    if r.status_code == 200:
        replies = r.json().get("replies", [])
        total = r.json().get("total", 0)
        print(f"     Replies: {len(replies)}, Total: {total}")

    # Empty reply (should fail)
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/replies",
        headers=header(TOKEN), json={"reply": ""})
    ok("Empty reply (should 400)", r, 400)

    # Too long reply
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/replies",
        headers=header(TOKEN), json={"reply": "x" * 1001})
    ok("Too long reply (should 400)", r, 400)

    # Reply without auth
    r = requests.post(f"{BASE}/api/comments/{COMMENT_ID}/replies",
        json={"reply": "no auth"})
    ok("Reply without auth (should 401)", r, 401)

    # Reply to non-existent comment
    r = requests.post(f"{BASE}/api/comments/99999999/replies",
        headers=header(TOKEN), json={"reply": "ghost"})
    ok("Reply to non-existent comment (should 404)", r, 404)

    # -- 9. REPLY REACTIONS --
    print("\n--- 9. Reply Reactions ---")
    if REPLY_ID:
        r = requests.post(f"{BASE}/api/replies/{REPLY_ID}/react",
            headers=header(TOKEN), json={"reaction": "like"})
        ok("Like a reply", r, 200)
        if r.status_code == 200:
            print(f"     Reply likes: {r.json().get('likes')}")

        r = requests.post(f"{BASE}/api/replies/{REPLY_ID}/react",
            headers=header(TOKEN), json={"reaction": "like"})
        ok("Toggle reply like off", r, 200)

        r = requests.post(f"{BASE}/api/replies/{REPLY_ID}/react",
            headers=header(TOKEN), json={"reaction": "dislike"})
        ok("Dislike a reply", r, 200)

    # -- 10. DELETE REPLY --
    print("\n--- 10. Delete Reply ---")
    if REPLY_ID:
        # Delete own reply
        r = requests.delete(f"{BASE}/api/replies/{REPLY_ID}",
            headers=header(TOKEN))
        ok("Delete own reply", r, 200)

        # Delete already-deleted reply
        r = requests.delete(f"{BASE}/api/replies/{REPLY_ID}",
            headers=header(TOKEN))
        ok("Delete non-existent reply (should 404)", r, 404)
else:
    print("  [SKIP] No comment for reply tests")

# -- 11. USER RECIPE CREATE --
print("\n--- 11. User Recipe: Create ---")
r = requests.post(f"{BASE}/api/recipes/create",
    headers=header(TOKEN),
    json={
        "name": f"Test Recipe by {test_user}",
        "description": "A delicious test recipe created during V3 testing.",
        "minutes": 30,
        "ingredients": ["2 cups flour", "1 cup sugar", "3 eggs", "butter"],
        "steps": [
            "Preheat oven to 350F",
            "Mix dry ingredients",
            "Add eggs and butter",
            "Pour into pan and bake for 25 minutes"
        ],
        "tags": ["test", "dessert", "baking"],
        "image_url": "https://example.com/test-recipe.jpg"
    })
ok("Create a recipe", r, 201)
CREATED_RECIPE_ID = None
if r.status_code == 201:
    data = r.json()
    CREATED_RECIPE_ID = data.get("recipe_id")
    print(f"     Created recipe id={CREATED_RECIPE_ID}")

# Create recipe - validation: missing name
r = requests.post(f"{BASE}/api/recipes/create",
    headers=header(TOKEN),
    json={"name": "", "ingredients": ["flour"], "steps": ["mix"]})
ok("Create recipe no name (should 400)", r, 400)

# Create recipe - validation: no ingredients
r = requests.post(f"{BASE}/api/recipes/create",
    headers=header(TOKEN),
    json={"name": "Test No Ingredients", "ingredients": [], "steps": ["step1"]})
ok("Create recipe no ingredients (should 400)", r, 400)

# Create recipe - validation: no steps
r = requests.post(f"{BASE}/api/recipes/create",
    headers=header(TOKEN),
    json={"name": "Test No Steps", "ingredients": ["flour"], "steps": []})
ok("Create recipe no steps (should 400)", r, 400)

# Create recipe - no auth
r = requests.post(f"{BASE}/api/recipes/create",
    json={"name": "Unauth Recipe", "ingredients": ["x"], "steps": ["y"]})
ok("Create recipe no auth (should 401)", r, 401)

# -- 12. USER RECIPE LIST --
print("\n--- 12. User Recipe: List ---")
r = requests.get(f"{BASE}/api/recipes/user", headers=header(TOKEN))
ok("Get user's recipes", r, 200)
if r.status_code == 200:
    user_recipes = r.json().get("recipes", [])
    print(f"     User has {len(user_recipes)} recipe(s)")

# No auth
r = requests.get(f"{BASE}/api/recipes/user")
ok("Get user recipes no auth (should 401)", r, 401)

# -- 13. USER RECIPE EDIT --
print("\n--- 13. User Recipe: Edit ---")
if CREATED_RECIPE_ID:
    r = requests.put(f"{BASE}/api/recipes/{CREATED_RECIPE_ID}/edit",
        headers=header(TOKEN),
        json={
            "name": f"Updated Recipe by {test_user}",
            "description": "Updated description after testing.",
            "minutes": 45,
            "ingredients": ["3 cups flour", "2 cups sugar", "4 eggs", "butter", "vanilla"],
            "steps": [
                "Preheat oven to 375F",
                "Sift dry ingredients together",
                "Beat eggs with sugar",
                "Combine and add vanilla",
                "Bake for 30 minutes"
            ],
            "tags": ["test", "updated", "baking", "vanilla"]
        })
    ok("Edit own recipe", r, 200)

    # Edit with invalid name
    r = requests.put(f"{BASE}/api/recipes/{CREATED_RECIPE_ID}/edit",
        headers=header(TOKEN),
        json={"name": "ab"})  # too short
    ok("Edit recipe short name (should 400)", r, 400)

# -- 14. PUBLIC USER RECIPES --
print("\n--- 14. Public User Recipes ---")
r = requests.get(f"{BASE}/api/user/{test_user}/recipes")
ok("Get public user recipes by username", r, 200)
if r.status_code == 200:
    print(f"     Public recipes: {len(r.json().get('recipes', []))}")

r = requests.get(f"{BASE}/api/user/nonexistent_user_xyz/recipes")
ok("Get recipes for non-existent user (should 404)", r, 404)

# -- 15. GET CREATED RECIPE DETAIL --
print("\n--- 15. Verify Created Recipe Detail ---")
if CREATED_RECIPE_ID:
    r = requests.get(f"{BASE}/api/recipe/{CREATED_RECIPE_ID}")
    ok("Get created recipe detail", r, 200)
    if r.status_code == 200:
        # API returns recipe fields directly (not nested under "recipe" key)
        recipe = r.json()
        recipe_name = recipe.get('name', '?')
        recipe_mins = recipe.get('minutes', '?')
        recipe_ings = recipe.get('ingredients', [])
        recipe_steps = recipe.get('steps', [])
        recipe_tags = recipe.get('tags', [])
        print(f"     Name: {recipe_name}")
        print(f"     Minutes: {recipe_mins}")
        print(f"     Ingredients: {len(recipe_ings)} => {recipe_ings[:3]}")
        print(f"     Steps: {len(recipe_steps)}")
        print(f"     Tags: {recipe_tags}")
        
        # Verify edited data persisted correctly
        expected_name = f"Updated Recipe by {test_user}"
        if recipe_name == expected_name:
            PASS += 1
            print(f"  [PASS] Recipe name matches after edit")
        else:
            FAIL += 1
            ERRORS.append(f"Recipe name mismatch: expected '{expected_name}', got '{recipe_name}'")
            print(f"  [FAIL] Recipe name mismatch: got '{recipe_name}'")
        
        if recipe_mins == 45:
            PASS += 1
            print(f"  [PASS] Recipe minutes matches after edit")
        else:
            FAIL += 1
            ERRORS.append(f"Recipe minutes mismatch: expected 45, got {recipe_mins}")
            print(f"  [FAIL] Recipe minutes mismatch: got {recipe_mins}")
        
        if len(recipe_ings) == 5:
            PASS += 1
            print(f"  [PASS] Recipe has 5 ingredients after edit")
        else:
            FAIL += 1
            ERRORS.append(f"Ingredients count: expected 5, got {len(recipe_ings)}")
            print(f"  [FAIL] Ingredients count: expected 5 got {len(recipe_ings)}")

        if len(recipe_steps) == 5:
            PASS += 1
            print(f"  [PASS] Recipe has 5 steps after edit")
        else:
            FAIL += 1
            ERRORS.append(f"Steps count: expected 5, got {len(recipe_steps)}")
            print(f"  [FAIL] Steps count: expected 5, got {len(recipe_steps)}")

# -- 16. DELETE USER RECIPE --
print("\n--- 16. User Recipe: Delete ---")
if CREATED_RECIPE_ID:
    r = requests.delete(f"{BASE}/api/recipes/{CREATED_RECIPE_ID}/delete",
        headers=header(TOKEN))
    ok("Delete own recipe", r, 200)

    # Double delete
    r = requests.delete(f"{BASE}/api/recipes/{CREATED_RECIPE_ID}/delete",
        headers=header(TOKEN))
    ok("Delete already-deleted recipe (should 404)", r, 404)

# -- 17. IMAGE UPLOAD --
print("\n--- 17. Image Upload ---")

import io, struct, zlib

def make_tiny_png(color=(255, 0, 0)):
    """Create a minimal valid 1x1 PNG in memory."""
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b'\x00' + bytes(color))
    idat = chunk(b'IDAT', raw)
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend

png_data = make_tiny_png()

# 17a. Upload with auth - valid PNG
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files={"image": ("test_recipe.png", io.BytesIO(png_data), "image/png")})
ok("Upload image (valid PNG)", r, 201)
UPLOADED_URL = None
if r.status_code == 201:
    data = r.json()
    UPLOADED_URL = data.get("image_url")
    assert data.get("success") is True, "success should be True"
    assert UPLOADED_URL and UPLOADED_URL.startswith("/api/uploads/"), f"Bad URL: {UPLOADED_URL}"
    print(f"     URL: {UPLOADED_URL}")

# 17b. Serve uploaded image
if UPLOADED_URL:
    r = requests.get(f"{BASE}{UPLOADED_URL}")
    ok("Serve uploaded image", r, 200)
    assert r.headers.get("Content-Type", "").startswith("image/"), "Should return image content-type"
    print(f"     Content-Type: {r.headers.get('Content-Type')}")

# 17c. Upload without auth
r = requests.post(f"{BASE}/api/upload/image",
    files={"image": ("test.png", io.BytesIO(png_data), "image/png")})
ok("Upload no auth (should 401)", r, 401)

# 17d. Upload with no file field
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"})
ok("Upload no file (should 400)", r, 400)

# 17e. Upload with empty filename
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files={"image": ("", io.BytesIO(b""), "image/png")})
ok("Upload empty filename (should 400)", r, 400)

# 17f. Upload invalid file type
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files={"image": ("script.exe", io.BytesIO(b"MZ\x90\x00"), "application/x-msdownload")})
ok("Upload invalid type .exe (should 400)", r, 400)

# 17g. Upload another invalid type (.txt)
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files={"image": ("notes.txt", io.BytesIO(b"hello"), "text/plain")})
ok("Upload invalid type .txt (should 400)", r, 400)

# 17h. Upload oversized file (>5MB)
big_data = b'\x00' * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files={"image": ("huge.png", io.BytesIO(big_data), "image/png")})
ok("Upload oversized file (should 400)", r, 400)

# 17i. Upload valid JPEG extension
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files={"image": ("photo.jpg", io.BytesIO(png_data), "image/jpeg")})
ok("Upload .jpg extension (allowed)", r, 201)

# 17j. Upload valid WEBP extension
r = requests.post(f"{BASE}/api/upload/image",
    headers={"Authorization": f"Bearer {TOKEN}"},
    files={"image": ("photo.webp", io.BytesIO(png_data), "image/webp")})
ok("Upload .webp extension (allowed)", r, 201)

# 17k. Create recipe with uploaded image URL
if UPLOADED_URL:
    r = requests.post(f"{BASE}/api/recipes/create",
        headers=header(TOKEN),
        json={
            "name": f"Uploaded Image Recipe {rand_str(4)}",
            "description": "Recipe with uploaded image",
            "minutes": 15,
            "ingredients": ["flour", "water"],
            "steps": ["mix", "cook"],
            "tags": ["test"],
            "image_url": UPLOADED_URL
        })
    ok("Create recipe with uploaded image URL", r, 201)
    UPLOAD_RECIPE_ID = r.json().get("recipe_id") if r.status_code == 201 else None

    # Verify the recipe stores the uploaded URL
    if UPLOAD_RECIPE_ID:
        r = requests.get(f"{BASE}/api/recipe/{UPLOAD_RECIPE_ID}")
        ok("Get recipe with uploaded image", r, 200)
        if r.status_code == 200:
            stored_url = r.json().get("image_url", "")
            if stored_url == UPLOADED_URL:
                PASS += 1
                print(f"  [PASS] Stored image_url matches uploaded URL")
            else:
                FAIL += 1
                ERRORS.append(f"Image URL mismatch: expected '{UPLOADED_URL}', got '{stored_url}'")
                print(f"  [FAIL] Image URL mismatch: '{stored_url}'")
        # Cleanup
        requests.delete(f"{BASE}/api/recipes/{UPLOAD_RECIPE_ID}/delete",
            headers=header(TOKEN))

# 17l. Serve non-existent image
r = requests.get(f"{BASE}/api/uploads/recipe_images/nonexistent_abc123.png")
ok("Serve non-existent image (should 404)", r, 404)

# -- 18. EDGE CASES --
print("\n--- 18. Edge Cases ---")
# Non-existent recipe comment
r = requests.get(f"{BASE}/api/recipe/99999999/comments")
ok("Comments for non-existent recipe", r, 200)  # Returns empty list, not 404

# React to non-existent comment
r = requests.post(f"{BASE}/api/comments/99999999/react",
    headers=header(TOKEN), json={"reaction": "like"})
ok("React to non-existent comment (should 404)", r, 404)

# Replies for non-existent comment
r = requests.get(f"{BASE}/api/comments/99999999/replies")
ok("Replies for non-existent comment", r, 200)  # Returns empty

# -- CLEANUP: Delete test comment --
print("\n--- Cleanup ---")
if COMMENT_ID:
    r = requests.delete(f"{BASE}/api/recipe/{RECIPE_ID}/comments/{COMMENT_ID}",
        headers=header(TOKEN))
    ok("Delete test comment", r, 200)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 70)
print(f"  TEST RESULTS: {PASS} PASSED, {FAIL} FAILED, {PASS + FAIL} TOTAL")
print("=" * 70)

if ERRORS:
    print("\n  FAILURES:")
    for i, e in enumerate(ERRORS, 1):
        print(f"    {i}. {e}")

if FAIL == 0:
    print("\n  ALL TESTS PASSED!")
else:
    print(f"\n  {FAIL} TEST(S) FAILED - see details above")

sys.exit(0 if FAIL == 0 else 1)
