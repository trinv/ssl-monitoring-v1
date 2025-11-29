#!/bin/bash

echo "=========================================="
echo "SSL Monitor - Authentication Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Navigate to project directory
cd "$(dirname "$0")"

echo ""
print_info "Step 1: Checking auth module files..."
if [ ! -d "backend/auth" ]; then
    print_error "backend/auth directory not found!"
    exit 1
fi

required_files=("backend/auth/__init__.py" "backend/auth/models.py" "backend/auth/utils.py" "backend/auth/dependencies.py" "backend/auth/routes.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Missing file: $file"
        exit 1
    fi
done
print_success "All auth module files present"

echo ""
print_info "Step 2: Checking database migration file..."
if [ ! -f "database/auth_migration.sql" ]; then
    print_error "database/auth_migration.sql not found!"
    exit 1
fi
print_success "Migration file found"

echo ""
print_info "Step 3: Stopping all services..."
docker compose down
if [ $? -ne 0 ]; then
    print_error "Failed to stop services"
    exit 1
fi
print_success "Services stopped"

echo ""
print_info "Step 4: Rebuilding backend image (this may take a minute)..."
docker compose build backend
if [ $? -ne 0 ]; then
    print_error "Failed to build backend image"
    exit 1
fi
print_success "Backend image built"

echo ""
print_info "Step 5: Starting all services..."
docker compose up -d
if [ $? -ne 0 ]; then
    print_error "Failed to start services"
    exit 1
fi
print_success "Services started"

echo ""
print_info "Step 6: Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker exec ssl-monitoring-postgres pg_isready -U ssluser > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    print_error "PostgreSQL did not become ready in time"
    exit 1
fi

echo ""
print_info "Step 7: Checking backend status..."
sleep 5
if docker ps | grep -q "ssl-monitor-backend"; then
    if docker logs ssl-monitor-backend 2>&1 | grep -q "FastAPI application started"; then
        print_success "Backend is running"
    else
        print_error "Backend started but may have errors. Check logs:"
        echo ""
        docker logs ssl-monitor-backend | tail -20
        exit 1
    fi
else
    print_error "Backend container is not running"
    exit 1
fi

echo ""
print_info "Step 8: Running authentication migration..."
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql > /dev/null 2>&1

if [ $? -eq 0 ]; then
    print_success "Migration completed"
else
    print_info "Migration may have already been applied (this is OK if tables exist)"
    # Check if tables exist
    tables_exist=$(docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('users', 'roles', 'permissions', 'sessions')")
    if [ "$tables_exist" -eq 4 ]; then
        print_success "Auth tables already exist"
    else
        print_error "Migration failed and tables don't exist"
        exit 1
    fi
fi

echo ""
print_info "Step 9: Verifying installation..."

# Check tables
echo "  - Checking database tables..."
tables=$(docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('users', 'roles', 'permissions', 'role_permissions', 'sessions', 'audit_logs') ORDER BY table_name")
table_count=$(echo "$tables" | wc -l)

if [ "$table_count" -eq 6 ]; then
    print_success "All 6 auth tables created"
else
    print_error "Expected 6 tables, found $table_count"
    echo "Tables found: $tables"
    exit 1
fi

# Check default admin user
echo "  - Checking admin user..."
admin_exists=$(docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -tAc "SELECT COUNT(*) FROM users WHERE username='admin'")
if [ "$admin_exists" -eq 1 ]; then
    print_success "Admin user exists"
else
    print_error "Admin user not found"
    exit 1
fi

# Check backend logs for errors
echo "  - Checking backend logs for errors..."
if docker logs ssl-monitor-backend 2>&1 | grep -qi "error\|traceback" | grep -v "Error handling"; then
    print_error "Backend has errors. Recent logs:"
    docker logs ssl-monitor-backend | tail -30
    exit 1
else
    print_success "No errors in backend logs"
fi

echo ""
echo "=========================================="
print_success "Authentication system deployed successfully!"
echo "=========================================="
echo ""
echo "📝 Next steps:"
echo "1. Access: http://localhost:8888"
echo "2. You will be redirected to login"
echo "3. Login with:"
echo "   Username: admin"
echo "   Password: Admin@123"
echo ""
echo "📊 Useful commands:"
echo "  View backend logs:  docker logs -f ssl-monitor-backend"
echo "  View database logs: docker logs -f ssl-monitoring-postgres"
echo "  Check services:     docker compose ps"
echo "  Stop services:      docker compose down"
echo ""
print_success "Deployment complete! 🎉"
