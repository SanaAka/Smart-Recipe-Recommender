# ✅ Setup Checklist - Smart Recipe Recommender

## Current Status:

### ✅ COMPLETED:
- [x] Project structure created
- [x] Frontend React app built
- [x] Backend Flask API created
- [x] ML recommendation system implemented
- [x] Database schema created
- [x] Python packages installed
- [x] Dataset downloaded and extracted
- [x] Data preprocessor configured for correct CSV file

### 📋 TODO - Complete These Steps:

## Step 1: Setup MySQL Database ⏱️ 5 min

**Choose one method:**

### Method A - MySQL Workbench (RECOMMENDED - Easiest):
```
1. Open MySQL Workbench
2. Connect to localhost
3. File → Open SQL Script
4. Select: D:\SSMMRR\database\schema.sql
5. Click Execute (⚡ lightning icon)
6. Verify "recipe_recommender" database appears in left panel
```

### Method B - Command Line:
```bash
mysql -u root -p
source D:/SSMMRR/database/schema.sql;
exit;
```

**Verify:** You should see a database named `recipe_recommender` with 7 tables.

---

## Step 2: Configure Database Password ⏱️ 2 min

```powershell
# Open the .env file
notepad D:\SSMMRR\backend\.env

# Find this line:
DB_PASSWORD=

# Change it to:
DB_PASSWORD=your_mysql_password

# Save and close
```

---

## Step 3: Load Recipe Data ⏱️ 10-30 min

### For QUICK TESTING (Recommended for first run):
```powershell
# Edit data_preprocessor.py first
notepad D:\SSMMRR\backend\data_preprocessor.py

# Change line 167 from:
    preprocessor.process_and_load(CSV_FILE, limit=5000)
# To:
    preprocessor.process_and_load(CSV_FILE, limit=1000)

# Save and run:
cd D:\SSMMRR\backend
.\venv\Scripts\Activate
python data_preprocessor.py
```

### For FULL DATASET (Takes longer):
```powershell
cd D:\SSMMRR\backend
.\venv\Scripts\Activate
python data_preprocessor.py
```

**What to expect:**
- You'll see: "Loading data from data/recipes_data.csv..."
- Then: "Loaded X recipes"
- Progress updates every 100 recipes
- Finally: "Successfully inserted X recipes into database"

---

## Step 4: Start Backend Server ⏱️ 1 min

**Open PowerShell Terminal 1:**
```powershell
cd D:\SSMMRR\backend
.\venv\Scripts\Activate
python app.py
```

**Expected output:**
```
Loading recipes from database...
Training TF-IDF model...
Model trained on X recipes
 * Running on http://0.0.0.0:5000
```

**✅ Keep this terminal running!**

---

## Step 5: Start Frontend ⏱️ 2 min

**Open PowerShell Terminal 2:**
```powershell
cd D:\SSMMRR\frontend
npm start
```

**Expected output:**
```
Compiled successfully!
You can now view recipe-recommender-frontend in the browser.

Local:            http://localhost:3000
```

**Browser should automatically open to http://localhost:3000**

---

## Step 6: Test the Application! 🎉

### Test 1: Get Recommendations
1. On home page, enter: `chicken, tomato, garlic`
2. Select dietary: `low-carb`
3. Select cuisine: `italian`
4. Click "Get Recommendations"
5. **Expected:** You see recipe cards with matching recipes

### Test 2: Search
1. Click "Search" in navigation
2. Search for: `pasta`
3. **Expected:** List of pasta recipes

### Test 3: Recipe Details
1. Click on any recipe card
2. **Expected:** Full recipe details with ingredients and steps

### Test 4: Favorites
1. Click the heart icon on a recipe
2. Click "Favorites" in navigation
3. **Expected:** Your saved recipe appears

---

## 🔍 Quick Diagnostics

### Check if MySQL is running:
```powershell
# Open Services
services.msc
# Look for "MySQL" or "MySQL80" - should be "Running"
```

### Check if database exists:
```bash
mysql -u root -p
SHOW DATABASES;
# Should see: recipe_recommender
USE recipe_recommender;
SHOW TABLES;
# Should see: recipes, ingredients, tags, etc.
```

### Check if data loaded:
```bash
mysql -u root -p
USE recipe_recommender;
SELECT COUNT(*) FROM recipes;
# Should show number > 0
```

### Check backend is running:
Open browser to: http://localhost:5000/api/health
Should see: `{"status":"healthy","message":"API is running"}`

---

## 🐛 Common Issues & Fixes

### "Can't connect to MySQL"
- **Fix:** Start MySQL service in Windows Services
- Or run: `net start MySQL80`

### "Unknown database 'recipe_recommender'"
- **Fix:** Run Step 1 again (execute schema.sql)

### "Access denied for user 'root'"
- **Fix:** Update password in backend\.env file

### "CSV file not found"
- **Fix:** Verify file at: D:\SSMMRR\backend\data\recipes_data.csv
- Should be ~2.3 GB

### "Port 5000 already in use"
```powershell
netstat -ano | findstr :5000
# Note the PID
taskkill /PID <PID> /F
```

### Frontend shows "Failed to fetch"
- **Fix:** Make sure backend is running on port 5000
- Check backend terminal for errors

---

## 📁 File Locations Reference

```
D:\SSMMRR\
├── backend\
│   ├── .env                    ← UPDATE THIS with MySQL password
│   ├── app.py                  ← Run this to start backend
│   ├── data\
│   │   └── recipes_data.csv    ← 2.3 GB dataset
│   ├── data_preprocessor.py    ← Run this to load data
│   └── venv\                   ← Virtual environment
├── frontend\
│   ├── src\                    ← React components
│   └── package.json
├── database\
│   └── schema.sql              ← Run this in MySQL
└── MANUAL_SETUP.md             ← Detailed instructions
```

---

## ✅ Final Verification

Before considering setup complete, verify:

- [ ] MySQL service is running
- [ ] Database `recipe_recommender` exists with 7 tables
- [ ] Backend .env has correct password
- [ ] Data loaded successfully (check count in recipes table)
- [ ] Backend running on http://localhost:5000
- [ ] Frontend running on http://localhost:3000
- [ ] Can see recommendations on home page
- [ ] Search works
- [ ] Can view recipe details
- [ ] Can save favorites

---

## 🎯 Next Steps After Setup

1. **Try different ingredient combinations**
2. **Test dietary filters** (vegan, keto, etc.)
3. **Explore different cuisines**
4. **Save your favorite recipes**
5. **Check the ML model accuracy** with various searches

---

## 📞 Need Help?

1. Check MANUAL_SETUP.md for detailed troubleshooting
2. Check README.md for complete documentation
3. Review error messages in terminal
4. Verify all steps completed in order

---

**Estimated Total Setup Time:** 20-40 minutes
**Quick Test Setup:** 10-15 minutes (with 1000 recipes)

Good luck! 🚀
