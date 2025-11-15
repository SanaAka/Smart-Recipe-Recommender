# Quick Setup Guide for Smart Recipe Recommender
# Follow these steps in order

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Smart Recipe Recommender - Quick Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "STEP 1: Database Setup" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "Option A - Using MySQL Workbench (Recommended):" -ForegroundColor White
Write-Host "  1. Open MySQL Workbench" -ForegroundColor Gray
Write-Host "  2. Connect to your MySQL server" -ForegroundColor Gray
Write-Host "  3. Click 'File' > 'Open SQL Script'" -ForegroundColor Gray
Write-Host "  4. Select: D:\SSMMRR\database\schema.sql" -ForegroundColor Gray
Write-Host "  5. Click the lightning bolt icon to execute" -ForegroundColor Gray
Write-Host ""
Write-Host "Option B - Using Command Line:" -ForegroundColor White
Write-Host "  Run these commands:" -ForegroundColor Gray
Write-Host '  mysql -u root -p' -ForegroundColor Green
Write-Host '  (enter password when prompted)' -ForegroundColor Gray
Write-Host '  Then in MySQL prompt:' -ForegroundColor Gray
Write-Host '  source D:/SSMMRR/database/schema.sql;' -ForegroundColor Green
Write-Host '  exit;' -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter after completing database setup"

Write-Host "`nSTEP 2: Update Backend Configuration" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "Edit the file: D:\SSMMRR\backend\.env" -ForegroundColor White
Write-Host "Update your MySQL password in the DB_PASSWORD field" -ForegroundColor Gray
Write-Host ""

$updateEnv = Read-Host "Would you like to update it now? (y/n)"
if ($updateEnv -eq 'y') {
    notepad D:\SSMMRR\backend\.env
    Write-Host "✓ Please save and close the file when done" -ForegroundColor Green
    Read-Host "Press Enter when you've saved the .env file"
}

Write-Host "`nSTEP 3: Load Recipe Data" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "This will take 10-30 minutes..." -ForegroundColor White
Write-Host ""

$loadData = Read-Host "Start loading data now? (y/n)"
if ($loadData -eq 'y') {
    cd D:\SSMMRR\backend
    Write-Host "`nLoading recipes into database..." -ForegroundColor Cyan
    python data_preprocessor.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓ Data loaded successfully!" -ForegroundColor Green
    } else {
        Write-Host "`n✗ Error loading data. Check the error messages above." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "To start the application:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Terminal 1 - Backend:" -ForegroundColor White
Write-Host "  cd D:\SSMMRR\backend" -ForegroundColor Gray
Write-Host "  .\venv\Scripts\Activate" -ForegroundColor Gray
Write-Host "  python app.py" -ForegroundColor Green
Write-Host ""
Write-Host "Terminal 2 - Frontend:" -ForegroundColor White
Write-Host "  cd D:\SSMMRR\frontend" -ForegroundColor Gray
Write-Host "  npm start" -ForegroundColor Green
Write-Host ""
Write-Host "Then visit: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
