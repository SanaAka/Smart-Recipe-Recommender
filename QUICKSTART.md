# Quick Start Guide - Smart Recipe Recommender

## Prerequisites Installation

### 1. Install Node.js
Download from: https://nodejs.org/
Verify installation:
```powershell
node --version
npm --version
```

### 2. Install Python
Download from: https://www.python.org/downloads/
Verify installation:
```powershell
python --version
```

### 3. Install MySQL
Download from: https://dev.mysql.com/downloads/mysql/
Or use MySQL Workbench: https://dev.mysql.com/downloads/workbench/

## Setup Steps

### Step 1: Database Setup (5 minutes)

```powershell
# Open MySQL command line or MySQL Workbench
mysql -u root -p

# In MySQL console:
source d:/SSMMRR/database/schema.sql;

# Or run manually:
CREATE DATABASE recipe_recommender;
```

### Step 2: Backend Setup (10 minutes)

```powershell
cd d:/SSMMRR/backend

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate

# Install packages
pip install -r requirements.txt

# Setup environment
Copy-Item .env.example .env

# Edit .env with your MySQL password
notepad .env
```

### Step 3: Download & Load Data (30-60 minutes)

1. Go to: https://www.kaggle.com/datasets/wilmerarltstrmberg/recipe-dataset-over-2m
2. Download the dataset
3. Extract `recipes.csv`
4. Create data folder:
   ```powershell
   mkdir data
   ```
5. Move `recipes.csv` to `backend/data/`
6. Load data:
   ```powershell
   python data_preprocessor.py
   ```

### Step 4: Frontend Setup (5 minutes)

```powershell
cd d:/SSMMRR/frontend
npm install
```

## Running the Application

### Terminal 1 - Backend
```powershell
cd d:/SSMMRR/backend
.\venv\Scripts\Activate
python app.py
```

### Terminal 2 - Frontend
```powershell
cd d:/SSMMRR/frontend
npm start
```

Visit: http://localhost:3000

## Testing the Application

1. On the home page, enter ingredients like: "chicken, tomato, garlic"
2. Select dietary preference (optional)
3. Select cuisine type (optional)
4. Click "Get Recommendations"
5. Click on any recipe to view details
6. Click the heart icon to save favorites

## Common Issues & Solutions

### "Module not found" error
```powershell
cd backend
.\venv\Scripts\Activate
pip install -r requirements.txt
```

### "Database connection failed"
- Check MySQL is running
- Verify credentials in `.env`
- Test connection: `mysql -u root -p`

### "Port 3000 already in use"
```powershell
# Kill the process
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### "Port 5000 already in use"
```powershell
# Change port in backend/.env
PORT=5001
# Update frontend/package.json proxy to "http://localhost:5001"
```

## File Checklist

Before running, ensure you have:
- ✅ MySQL installed and running
- ✅ Database created (`recipe_recommender`)
- ✅ Python virtual environment created
- ✅ Backend dependencies installed
- ✅ `.env` file configured
- ✅ Dataset downloaded and processed
- ✅ Frontend dependencies installed

## Next Steps

After setup:
1. Explore the recommendation system
2. Try different ingredient combinations
3. Save your favorite recipes
4. Use the search functionality
5. Check out recipe details

## Support

If you encounter issues:
1. Check the main README.md for detailed troubleshooting
2. Verify all prerequisites are installed
3. Check that both backend and frontend are running
4. Review console logs for error messages

Happy Cooking! 🍳
