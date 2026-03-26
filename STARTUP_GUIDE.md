# 🚀 Quick Start Guide - New Features

## Prerequisites Completed ✅
- Database schema updated (comments table created)
- Python `requests` library installed
- Python cache cleared
- All new endpoints added to backend
- Frontend components created

## Start the Application

### Option 1: Quick Start (Recommended)
```powershell
# Terminal 1 - Backend
cd D:\SSMMRR\backend
python app_v2.py

# Terminal 2 - Frontend  
cd D:\SSMMRR\frontend
npm start
```

### Option 2: Check Everything First
```powershell
# 1. Verify database schema
cd D:\SSMMRR\backend
python add_comments_schema.py

# 2. Clear cache (already done)
Remove-Item -Path "__pycache__" -Recurse -Force

# 3. Start backend
python app_v2.py

# 4. Start frontend (new terminal)
cd ..\frontend
npm start
```

## Test the New Features

### 1. **Star Ratings** ⭐
1. Navigate to any recipe detail page
2. You'll see the star rating below the recipe header
3. If not logged in, stars show read-only average rating
4. **Login first** at http://localhost:3000/login
5. After login, click stars to rate (1-5)
6. Your rating is saved and average updates instantly

### 2. **Comments System** 💬
1. Scroll to bottom of recipe detail page
2. See the comments section
3. **Login required** to post comments
4. Type your comment (3-1000 characters)
5. Click "Post Comment"
6. Your comment appears instantly
7. Delete your own comments with 🗑️ button

### 3. **Pagination** 📜
Test with API directly:
```powershell
# Browse recipes (page 1)
Invoke-RestMethod -Uri "http://localhost:5000/api/recipes/browse?page=1&limit=10&sort=rating"

# Page 2
Invoke-RestMethod -Uri "http://localhost:5000/api/recipes/browse?page=2&limit=10&sort=popular"

# With filters
Invoke-RestMethod -Uri "http://localhost:5000/api/recipes/browse?max_time=30&max_calories=400"
```

### 4. **Authentication** 🔐
Already working! Test it:
```powershell
# Register new user
$body = @{
    username = "testuser"
    email = "test@example.com"
    password = "Test123!"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" -Method POST -Body $body -ContentType "application/json"

# Login
$loginBody = @{
    username = "testuser"
    password = "Test123!"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
$token = $response.access_token
Write-Host "Token: $token"
```

### 5. **Unsplash Images** 🖼️
**Note:** Requires free API key from https://unsplash.com/developers

1. Get your Unsplash Access Key
2. Edit `backend\.env`:
   ```env
   UNSPLASH_ACCESS_KEY=your-actual-key-here
   ```
3. Restart backend server
4. Test image search:
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5000/api/recipe/1/image/search"
   ```

## Expected Behavior

### ✅ Working Search (After Restart)
```powershell
# Should return recipes now (cuisine column removed)
Invoke-RestMethod -Uri "http://localhost:5000/api/search?query=chicken&type=name&limit=5"
```

If you see results, the search fix is working! 🎉

### ✅ New Endpoints Available
- `GET /api/recipe/:id/rating` - View ratings
- `POST /api/recipe/:id/rating` - Submit rating (auth required)
- `GET /api/recipe/:id/comments` - View comments
- `POST /api/recipe/:id/comments` - Add comment (auth required)
- `DELETE /api/recipe/:id/comments/:id` - Delete comment (auth required)
- `GET /api/recipe/:id/image/search` - Search Unsplash
- `POST /api/recipe/:id/image` - Update image (auth required)
- `GET /api/recipes/browse` - Browse with pagination

## Troubleshooting

### Backend Won't Start
```powershell
# Check for port conflicts
Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue

# Kill existing Python processes
Get-Process python | Stop-Process -Force
```

### Frontend Errors
```powershell
# Reinstall dependencies
cd D:\SSMMRR\frontend
Remove-Item -Path "node_modules" -Recurse -Force
npm install
npm start
```

### Database Errors
```powershell
# Re-run schema migration
cd D:\SSMMRR\backend
python add_comments_schema.py
```

### Module Import Errors
```powershell
# Clear Python cache
cd D:\SSMMRR\backend
Remove-Item -Path "__pycache__" -Recurse -Force
Remove-Item -Path "*.pyc" -Recurse -Force
```

## Features Summary

| Feature | Status | Auth Required | Endpoint |
|---------|--------|---------------|----------|
| Search Fix | ✅ Fixed | No | `/api/search` |
| Star Ratings | ✅ New | Yes (submit) | `/api/recipe/:id/rating` |
| Comments | ✅ New | Yes (post) | `/api/recipe/:id/comments` |
| Pagination | ✅ New | No | `/api/recipes/browse` |
| Authentication | ✅ Existing | - | `/api/auth/*` |
| Unsplash Images | ✅ New | No (search), Yes (update) | `/api/recipe/:id/image/*` |

## Quick Test Script

Save as `test_features.ps1` and run:
```powershell
$base = "http://localhost:5000"

Write-Host "Testing new features..." -ForegroundColor Cyan

# Test ratings
Write-Host "`n1. Rating Stats:" -ForegroundColor Yellow
Invoke-RestMethod -Uri "$base/api/recipe/1/rating"

# Test comments
Write-Host "`n2. Comments:" -ForegroundColor Yellow
Invoke-RestMethod -Uri "$base/api/recipe/1/comments?page=1&limit=5"

# Test pagination
Write-Host "`n3. Browse Recipes:" -ForegroundColor Yellow
$browse = Invoke-RestMethod -Uri "$base/api/recipes/browse?page=1&limit=3&sort=rating"
Write-Host "Total recipes: $($browse.total)"
Write-Host "Has more: $($browse.has_more)"

# Test search (fixed)
Write-Host "`n4. Search:" -ForegroundColor Yellow
$search = Invoke-RestMethod -Uri "$base/api/search?query=pasta&type=name&limit=3"
Write-Host "Found: $($search.results.Count) recipes"

Write-Host "`n✅ All tests complete!" -ForegroundColor Green
```

## What's Next?

1. **Start the servers** (backend + frontend)
2. **Open** http://localhost:3000
3. **Login** with existing account or register new one
4. **Browse recipes** and test ratings
5. **Leave comments** on your favorite recipes
6. **Enjoy the enhanced social features!** 🎉

## Support

If you encounter any issues:
1. Check backend terminal for errors
2. Check browser console (F12)
3. Verify database connection
4. Clear Python cache
5. Restart both servers

---

**All systems ready! Start cooking with your enhanced recipe app! 🍳**
