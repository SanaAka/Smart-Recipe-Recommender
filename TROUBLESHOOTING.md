# Alternative Installation Guide - When Full Install Fails

## Problem: Pandas/NumPy compilation errors

### Solution 1: Install Pre-built Wheels (RECOMMENDED)

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install with pre-built wheels
pip install --only-binary :all: -r requirements.txt
```

### Solution 2: Install Minimal Version First

```powershell
# Install just what's needed for the API (no ML)
pip install -r requirements_minimal.txt

# Test if app starts
python app_v2.py

# Install ML libraries separately later
pip install pandas==2.0.3 numpy==1.24.3 scikit-learn==1.3.2
```

### Solution 3: Use Anaconda/Miniconda (Easiest)

```powershell
# Download and install Miniconda from: https://docs.conda.io/en/latest/miniconda.html

# Create environment
conda create -n recipe python=3.10
conda activate recipe

# Install packages
pip install -r requirements.txt
```

## Problem: MySQL command not found

### Solution: Add MySQL to PATH or use full path

**Option A: Use MySQL Workbench**
1. Open MySQL Workbench
2. Connect to your server
3. File → Run SQL Script
4. Select `database\user_management_schema.sql`
5. Execute

**Option B: Find MySQL executable**
```powershell
# Find MySQL installation
Get-ChildItem "C:\Program Files\MySQL" -Recurse -Filter mysql.exe

# Use full path (example)
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p recipe_recommender
```

**Option C: Add MySQL to PATH**
```powershell
# Add to PATH temporarily
$env:Path += ";C:\Program Files\MySQL\MySQL Server 8.0\bin"

# Now try again
Get-Content database\user_management_schema.sql | mysql -u root -p recipe_recommender
```

**Option D: Skip User Tables for Now**
You can run the app without user management tables initially. The app will work with the original tables for recipes.

## Problem: pytest not found

### Solution: Install pytest or use python -m pytest

```powershell
# Check if pytest is installed
pip show pytest

# If not installed
pip install pytest pytest-cov pytest-flask

# Run tests with python -m
python -m pytest tests/ -v --cov=.

# Or activate virtual environment first
.\venv\Scripts\Activate
pytest tests/ -v
```

## Quick Start Without Issues

**Step 1: Minimal Install**
```powershell
cd D:\SSMMRR\backend
pip install -r requirements_minimal.txt
```

**Step 2: Create .env**
```powershell
# Already done
# Make sure DB_PASSWORD is set
```

**Step 3: Skip Database Migration (Optional)**
The original tables still work! User management is optional.

**Step 4: Start Server**
```powershell
python app_v2.py
```

**Step 5: Test**
```powershell
# In another terminal
Invoke-RestMethod http://localhost:5000/api/health
```

## Working Without User Management

If you can't install the user tables, you can still use:
- ✅ Recipe search
- ✅ Recommendations (ML)
- ✅ Recipe details
- ❌ User registration/login (requires user tables)
- ❌ Persistent favorites (requires user tables)

The app will work fine without user management tables!

## Alternative: Use Original app.py

If app_v2.py has too many dependencies:

```powershell
# Use the original app (works with existing setup)
python app.py
```

Then gradually upgrade when dependencies are resolved.

## Getting Help

If still having issues:
1. Check Python version: `python --version` (need 3.8+)
2. Check pip version: `pip --version`
3. Try: `pip install --upgrade pip setuptools wheel`
4. Consider using Docker instead: `docker-compose up -d`
