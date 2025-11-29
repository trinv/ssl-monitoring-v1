#!/bin/bash

echo "=========================================="
echo "Applying Simple Authentication"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${YELLOW}This will replace complex auth with simple version:${NC}"
echo "  - Only 2 roles: admin, user"
echo "  - Simple login: username + password"
echo "  - No session expiry, audit logs, etc."
echo "  - Port 80 for frontend (not 8888)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "[1/5] Backing up original files..."
mkdir -p backup
cp backend/auth/models.py backup/models.py.backup 2>/dev/null || true
cp backend/auth/routes.py backup/routes.py.backup 2>/dev/null || true
cp backend/auth/dependencies.py backup/dependencies.py.backup 2>/dev/null || true
cp frontend/js/auth.js backup/auth.js.backup 2>/dev/null || true
echo -e "${GREEN}✅ Backup created in backup/folder${NC}"

echo ""
echo "[2/5] Replacing backend auth files..."
cp backend/auth/simple_models.py backend/auth/models.py
cp backend/auth/simple_routes.py backend/auth/routes.py
cp backend/auth/simple_dependencies.py backend/auth/dependencies.py
echo -e "${GREEN}✅ Backend files updated${NC}"

echo ""
echo "[3/5] Replacing frontend auth file..."
cp frontend/js/simple_auth.js frontend/js/auth.js
echo -e "${GREEN}✅ Frontend file updated${NC}"

echo ""
echo "[4/5] Running database migration..."
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database migration completed${NC}"
else
    echo -e "${YELLOW}⚠️  Migration may have already been applied${NC}"
fi

echo ""
echo "[5/5] Restarting backend..."
docker compose restart backend
sleep 5
echo -e "${GREEN}✅ Backend restarted${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}Simple Authentication Applied!${NC}"
echo "=========================================="
echo ""
echo "Access your application:"
echo "  Frontend: http://YOUR_SERVER (port 80)"
echo "  Backend:  http://YOUR_SERVER:8080"
echo "  API Docs: http://YOUR_SERVER:8080/docs"
echo ""
echo "Login credentials:"
echo "  Username: admin"
echo "  Password: Admin@123"
echo ""
echo "Features:"
echo "  ✅ Simple login (username + password)"
echo "  ✅ 2 roles: admin (full), user (limited)"
echo "  ✅ Admin can manage users"
echo "  ✅ Users can change password"
echo ""
echo "See SIMPLE_AUTH_GUIDE.md for details"
