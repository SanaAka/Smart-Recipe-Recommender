# Database Setup Script for PowerShell
# Run this to create the database schema

Write-Host "Creating database and schema..." -ForegroundColor Cyan

# Read the SQL file content
$sqlContent = Get-Content -Path "D:\SSMMRR\database\schema.sql" -Raw

# Execute MySQL command
try {
    $sqlContent | mysql -u root -p
    Write-Host "`nDatabase schema created successfully!" -ForegroundColor Green
} catch {
    Write-Host "`nError: Failed to create database schema" -ForegroundColor Red
    Write-Host "Please check your MySQL credentials and try again" -ForegroundColor Yellow
    exit 1
}
