#!/bin/bash
# Verify project structure after optimization

echo "🔍 Verifying SSL Monitor Project Structure..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
FAILED=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1"
        ((SUCCESS++))
    else
        echo -e "${RED}❌${NC} $1 - MISSING"
        ((FAILED++))
    fi
}

check_not_exists() {
    if [ ! -e "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 - Correctly removed"
        ((SUCCESS++))
    else
        echo -e "${RED}❌${NC} $1 - Should be deleted"
        ((FAILED++))
    fi
}

echo "=== Required Files ==="
check_file ".env"
check_file ".env.example"
check_file "docker-compose.yml"
check_file "CHANGELOG.md"
check_file "OPTIMIZATION_SUMMARY.md"
check_file "DEPLOYMENT.md"

echo ""
echo "=== Backend Files ==="
check_file "backend/main.py"
check_file "backend/database.py"
check_file "backend/models.py"
check_file "backend/auth.py"
check_file "backend/requirements.txt"
check_file "backend/Dockerfile"
check_file "backend/routes/__init__.py"
check_file "backend/routes/auth.py"
check_file "backend/routes/domains.py"
check_file "backend/routes/scan.py"

echo ""
echo "=== Scanner Files ==="
check_file "scanner/main.py"
check_file "scanner/scanner.py"
check_file "scanner/requirements.txt"
check_file "scanner/Dockerfile"

echo ""
echo "=== Database Files ==="
check_file "database/init.sql"

echo ""
echo "=== Frontend Files ==="
check_file "frontend/index.html"
check_file "frontend/css/style.css"

echo ""
echo "=== Nginx Files ==="
check_file "nginx/nginx.conf"

echo ""
echo "=== Files That Should Be Deleted ==="
check_not_exists "backend/auth/"
check_not_exists "frontend/index.html.backup"
check_not_exists "frontend/index_old.html"
check_not_exists "database/simple_auth_migration.sql"

echo ""
echo "=== Checking Important Content ==="

# Check .env has strong passwords
if grep -q "CHANGE_ME" .env 2>/dev/null; then
    echo -e "${YELLOW}⚠️${NC} .env still has CHANGE_ME placeholders - UPDATE BEFORE DEPLOY"
    ((FAILED++))
else
    echo -e "${GREEN}✅${NC} .env passwords appear to be customized"
    ((SUCCESS++))
fi

# Check JWT_SECRET length in .env
JWT_LEN=$(grep "^JWT_SECRET=" .env 2>/dev/null | cut -d'=' -f2 | wc -c)
if [ "$JWT_LEN" -gt 32 ]; then
    echo -e "${GREEN}✅${NC} JWT_SECRET is strong (${JWT_LEN} chars)"
    ((SUCCESS++))
else
    echo -e "${RED}❌${NC} JWT_SECRET is too short (${JWT_LEN} chars) - should be 32+"
    ((FAILED++))
fi

# Check docker-compose doesn't have hardcoded passwords
if grep -q "SSL@Pass123" docker-compose.yml 2>/dev/null; then
    echo -e "${RED}❌${NC} docker-compose.yml still has hardcoded password"
    ((FAILED++))
else
    echo -e "${GREEN}✅${NC} docker-compose.yml uses environment variables"
    ((SUCCESS++))
fi

# Check scanner has json import
if grep -q "^import json" scanner/scanner.py 2>/dev/null; then
    echo -e "${GREEN}✅${NC} scanner.py has json import"
    ((SUCCESS++))
else
    echo -e "${RED}❌${NC} scanner.py missing json import"
    ((FAILED++))
fi

# Check routes/auth.py has datetime import
if grep -q "from datetime import datetime" backend/routes/auth.py 2>/dev/null; then
    echo -e "${GREEN}✅${NC} routes/auth.py has datetime import"
    ((SUCCESS++))
else
    echo -e "${RED}❌${NC} routes/auth.py missing datetime import"
    ((FAILED++))
fi

echo ""
echo "================================"
echo "📊 VERIFICATION RESULTS"
echo "================================"
echo -e "${GREEN}Success: ${SUCCESS}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED! Project is ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review and fix issues above.${NC}"
    exit 1
fi
