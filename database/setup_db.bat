@echo off
REM Database Setup Script for Windows
REM Run this script to create the database schema

echo Creating database and schema...
mysql -u root -p -e "source D:/SSMMRR/database/schema.sql"

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to create database schema
    echo Please check your MySQL credentials and try again
    pause
    exit /b 1
)

echo.
echo Database schema created successfully!
pause
