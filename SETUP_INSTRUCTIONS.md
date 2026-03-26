# Quick Setup Guide - Recipe Recommender v2.0

## Step 1: Install Dependencies

```powershell
cd backend
pip install -r requirements.txt
```

## Step 2: Setup Database

```powershell
# From project root (D:\SSMMRR)
Get-Content database\user_management_schema.sql | mysql -u root -p
# Enter your MySQL password when prompted
```

## Step 3: Run Tests

```powershell
cd backend
pytest tests/ -v --cov=.
```

## Step 4: Start Application

### Option A: Direct Python (Recommended for development)
```powershell
cd backend
python app_v2.py
```

### Option B: Docker (Production-like)
```powershell
# From project root
docker-compose up -d
```

## Step 5: Test API

```powershell
curl http://localhost:5000/api/health
```

## Common Issues

### Issue: pytest not found
**Solution:**
```powershell
cd backend
pip install pytest pytest-cov pytest-flask
```

### Issue: MySQL import fails in PowerShell
**Solution:** Use `Get-Content` instead of `<`:
```powershell
Get-Content database\user_management_schema.sql | mysql -u root -p recipe_recommender
```

### Issue: Docker environment variables not set
**Solution:** Ensure `.env.docker` exists in project root:
```powershell
# Check if file exists
Test-Path .env.docker
# Should return: True
```

### Issue: Wrong path for app_v2.py
**Solution:**
```powershell
# From backend directory:
python app_v2.py

# From project root:
python backend/app_v2.py
```

## Environment Setup

Create `.env` file in `backend/` directory:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=recipe_recommender
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret
```

## Verification

After setup, verify everything works:

```powershell
# 1. Check database tables
mysql -u root -p -e "USE recipe_recommender; SHOW TABLES;"

# 2. Run tests
cd backend
pytest tests/ -v

# 3. Start server
python app_v2.py

# 4. Test health endpoint (in another terminal)
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "ml_ready": false,
  "ml_loading": true,
  "database": "connected"
}
```

## Next Steps

1. Read `SECURITY_AND_IMPROVEMENTS.md` for full documentation
2. Review `QUICK_REFERENCE.md` for API examples
3. Check `IMPROVEMENTS_SUMMARY.md` for what's new
