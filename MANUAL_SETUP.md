# 🚀 MANUAL SETUP INSTRUCTIONS

## What You Have:
✅ Python packages installed in backend
✅ Dataset extracted at: `D:\SSMMRR\backend\data\recipes_data.csv`
✅ All code files created

## What You Need to Do:

### 1️⃣ Setup MySQL Database (5 minutes)

**Option A - MySQL Workbench (Easiest):**
1. Open **MySQL Workbench**
2. Connect to your local MySQL server
3. Click **File → Open SQL Script**
4. Select: `D:\SSMMRR\database\schema.sql`
5. Click the ⚡ **Execute** button (lightning bolt icon)
6. Verify you see "recipe_recommender" database created

**Option B - Command Line:**
```bash
# Open MySQL command line client (comes with MySQL installation)
mysql -u root -p
# Enter your password

# Then run:
source D:/SSMMRR/database/schema.sql;
exit;
```

### 2️⃣ Configure Backend (2 minutes)

1. Open: `D:\SSMMRR\backend\.env`
2. Update the MySQL password line:
   ```
   DB_PASSWORD=your_actual_mysql_password
   ```
3. Save the file

### 3️⃣ Load Recipe Data (10-30 minutes)

```powershell
cd D:\SSMMRR\backend
.\venv\Scripts\Activate
python data_preprocessor.py
```

This will:
- Read the 2M+ recipes from CSV
- Process and clean the data
- Load into MySQL database
- **Be patient!** This takes time due to the large dataset

You can reduce the number of recipes by editing `data_preprocessor.py` line 167:
```python
preprocessor.process_and_load(CSV_FILE, limit=1000)  # Change 5000 to 1000 for faster testing
```

### 4️⃣ Start the Application

**Terminal 1 - Backend:**
```powershell
cd D:\SSMMRR\backend
.\venv\Scripts\Activate
python app.py
```

**Terminal 2 - Frontend:**
```powershell
cd D:\SSMMRR\frontend
npm start
```

### 5️⃣ Use the App! 🎉

Visit: **http://localhost:3000**

Try entering:
- Ingredients: `chicken, tomato, garlic`
- Dietary: `low-carb`
- Cuisine: `italian`

---

## 🔧 Troubleshooting

### MySQL Connection Error
```
Can't connect to MySQL server
```
**Fix:** Make sure MySQL is running. Check Windows Services or start MySQL from the Start menu.

### Database doesn't exist
```
Unknown database 'recipe_recommender'
```
**Fix:** Run the schema.sql file again (Step 1)

### Password error
```
Access denied for user 'root'
```
**Fix:** Update the password in `backend/.env` file

### CSV file not found
```
Error: CSV file not found
```
**Fix:** Verify the file exists at `D:\SSMMRR\backend\data\recipes_data.csv`

### Port already in use
```
Port 5000 is already in use
```
**Fix:** 
```powershell
# Find and kill the process
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F
```

---

## 📊 Expected Results

After loading data, you should see:
- **~5,000+ recipes** in database (or however many you configured)
- Backend running on `http://localhost:5000`
- Frontend running on `http://localhost:3000`
- ML model trained and ready

---

## ⏱️ Time Estimates

- Database setup: **5 minutes**
- Configuration: **2 minutes**
- Data loading (5000 recipes): **15-20 minutes**
- Data loading (full 2M+ recipes): **2-4 hours** (not recommended for first run)

---

## 💡 Quick Test Setup

For **fast testing**, use only 1000 recipes:

Edit `backend/data_preprocessor.py` line 167:
```python
preprocessor.process_and_load(CSV_FILE, limit=1000)
```

This will load in ~5 minutes and is perfect for testing the app!

---

## ✅ Verification Checklist

Before running the app, verify:
- [ ] MySQL is running
- [ ] Database `recipe_recommender` exists
- [ ] Backend `.env` file has correct MySQL password
- [ ] Data has been loaded (check terminal for "Successfully inserted X recipes")
- [ ] Virtual environment is activated for backend
- [ ] Both terminals are running (backend & frontend)

---

Need help? Check the full README.md for more details!
