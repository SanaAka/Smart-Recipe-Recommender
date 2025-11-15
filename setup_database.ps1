# Setup Script for Smart Recipe Recommender
# Run this script to set up the database

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Smart Recipe Recommender - Database Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Prompt for MySQL password
$password = Read-Host "Enter your MySQL root password" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

Write-Host "`nCreating database and tables..." -ForegroundColor Yellow

# Read the SQL file
$sqlFile = "D:\SSMMRR\database\schema.sql"
$sqlContent = Get-Content -Path $sqlFile -Raw

# Save to temp file for mysql command
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sqlContent | Out-File -FilePath $tempFile -Encoding UTF8

try {
    # Execute MySQL command
    & mysql -u root -p"$plainPassword" < $tempFile 2>&1 | Write-Host
    
    Write-Host "`n✓ Database created successfully!" -ForegroundColor Green
    Write-Host "`nDatabase: recipe_recommender" -ForegroundColor Cyan
    Write-Host "Tables created: recipes, ingredients, tags, nutrition, steps, and junction tables" -ForegroundColor Cyan
    
} catch {
    Write-Host "`n✗ Error creating database" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    # Clean up temp file
    if (Test-Path $tempFile) {
        Remove-Item $tempFile
    }
}

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Run: python data_preprocessor.py" -ForegroundColor White
Write-Host "2. Wait for data to load (10-30 minutes)" -ForegroundColor White
Write-Host "3. Start the backend: python app.py" -ForegroundColor White
