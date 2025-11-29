@echo off
echo ==========================================
echo Creating Authentication Tables
echo ==========================================
echo.

cd /d "%~dp0"

echo [Step 1] Checking PostgreSQL container...
docker ps | findstr "ssl-monitoring-postgres" > nul
if errorlevel 1 (
    echo ERROR: PostgreSQL container is not running!
    echo.
    echo Please start it first:
    echo   docker compose up -d
    echo.
    pause
    exit /b 1
)
echo OK: PostgreSQL is running
echo.

echo [Step 2] Creating authentication tables...
echo This will create:
echo   - roles table (admin, user)
echo   - users table
echo   - sessions table
echo   - Default admin user (admin/Admin@123)
echo.

type database\simple_auth_migration.sql | docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor

if errorlevel 1 (
    echo.
    echo WARNING: Migration may have failed or tables already exist.
    echo.
) else (
    echo.
    echo SUCCESS: Tables created!
    echo.
)

echo [Step 3] Verifying tables...
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "\dt" | findstr "users"
if errorlevel 1 (
    echo ERROR: Users table not found!
    echo.
    pause
    exit /b 1
)
echo OK: Tables exist
echo.

echo [Step 4] Checking admin user...
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT username FROM users WHERE username='admin'" | findstr "admin"
if errorlevel 1 (
    echo ERROR: Admin user not found!
    echo.
    pause
    exit /b 1
)
echo OK: Admin user exists
echo.

echo ==========================================
echo SUCCESS! Authentication Ready!
echo ==========================================
echo.
echo You can now login:
echo   URL:      http://YOUR_SERVER
echo   Username: admin
echo   Password: Admin@123
echo.
echo Press any key to exit...
pause >nul
