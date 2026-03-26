# Quick Setup Script for Recipe Recommender v2.0
# This script helps you set up the improved version

Write-Host "=== Recipe Recommender v2.0 Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if .env.docker exists
if (-not (Test-Path ".env.docker")) {
    Write-Host "Creating .env.docker file..." -ForegroundColor Yellow
    Copy-Item ".env.docker" ".env.docker.local"
    
    # Generate secure keys
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $jwtKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $mysqlRootPass = -join ((65..90) + (97..122) + (48..57) + (33, 64, 35, 36, 37) | Get-Random -Count 20 | ForEach-Object {[char]$_})
    $mysqlUserPass = -join ((65..90) + (97..122) + (48..57) + (33, 64, 35, 36, 37) | Get-Random -Count 20 | ForEach-Object {[char]$_})
    
    # Update .env.docker.local with generated passwords
    (Get-Content ".env.docker.local") `
        -replace 'your_secure_root_password_here', $mysqlRootPass `
        -replace 'your_secure_user_password_here', $mysqlUserPass `
        -replace 'generate_a_secure_random_key_here', $secretKey `
        -replace 'generate_another_secure_random_key_here', $jwtKey |
        Set-Content ".env.docker.local"
    
    Write-Host "✓ Created .env.docker.local with secure passwords" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Keep .env.docker.local secure and never commit it!" -ForegroundColor Red
} else {
    Write-Host "✓ .env.docker already exists" -ForegroundColor Green
}

# Check Python dependencies
Write-Host ""
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
cd backend

if (Test-Path "venv") {
    Write-Host "✓ Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

Write-Host ""
Write-Host "Installing/updating Python packages..." -ForegroundColor Yellow
.\venv\Scripts\Activate
pip install -r requirements.txt --upgrade
Write-Host "✓ Python packages installed" -ForegroundColor Green

# Run database migration
Write-Host ""
Write-Host "Database setup..." -ForegroundColor Yellow
Write-Host "To run database migrations, execute:" -ForegroundColor Cyan
Write-Host '  Get-Content database\user_management_schema.sql | mysql -u root -p' -ForegroundColor White

# Run tests
Write-Host ""
$runTests = Read-Host "Run unit tests? (y/n)"
if ($runTests -eq 'y') {
    Write-Host "Running tests..." -ForegroundColor Yellow
    pytest tests/ -v --cov=. --cov-report=html
    Write-Host ""
    Write-Host "✓ Tests complete! View coverage at backend/htmlcov/index.html" -ForegroundColor Green
}

# Setup complete
Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run database migrations (see command above)" -ForegroundColor White
Write-Host "2. Start the application:" -ForegroundColor White
Write-Host "   Option A: python backend/app_v2.py" -ForegroundColor Gray
Write-Host "   Option B: docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test the API:" -ForegroundColor White
Write-Host "   curl http://localhost:5000/api/health" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Read SECURITY_AND_IMPROVEMENTS.md for full documentation" -ForegroundColor White
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Green
