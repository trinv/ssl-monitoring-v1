#!/bin/bash
# Fix Database Issues

echo "=========================================="
echo " Domain Monitor - Database Fix"
echo "=========================================="
echo ""

echo "This script will:"
echo "1. Stop all services"
echo "2. Remove old database data"
echo "3. Recreate fresh database"
echo "4. Initialize with admin user"
echo ""
echo "⚠️  WARNING: This will DELETE all existing data!"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "Step 1: Stopping services..."
docker-compose down

echo ""
echo "Step 2: Removing old volumes..."
docker volume rm domain-monitor_postgres_data 2>/dev/null || echo "Volume already removed or doesn't exist"

echo ""
echo "Step 3: Starting services..."
docker-compose up -d

echo ""
echo "Step 4: Waiting for PostgreSQL to initialize (30 seconds)..."
sleep 30

echo ""
echo "Step 5: Checking database..."
if docker-compose exec -T postgres psql -U domainuser -d domains -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection OK"
else
    echo "❌ Database still not ready. Checking logs..."
    docker-compose logs postgres | tail -20
    exit 1
fi

echo ""
echo "Step 6: Verifying tables..."
TABLES=$(docker-compose exec -T postgres psql -U domainuser -d domains -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
echo "Found $TABLES tables"

if [ "$TABLES" -lt "5" ]; then
    echo "⚠️  Tables not initialized. Running init script manually..."
    docker-compose exec -T postgres psql -U domainuser -d domains < database/init.sql
fi

echo ""
echo "Step 7: Verifying admin user..."
ADMIN_COUNT=$(docker-compose exec -T postgres psql -U domainuser -d domains -t -c "SELECT COUNT(*) FROM users WHERE username = 'admin';" 2>/dev/null | tr -d ' ')
echo "Admin user count: $ADMIN_COUNT"

if [ "$ADMIN_COUNT" -eq "0" ]; then
    echo "Creating admin user..."
    docker-compose exec -T postgres psql -U domainuser -d domains << 'SQL'
INSERT INTO users (username, password_hash, email, is_active) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XnVx4L8sCYDS', 'admin@domain-monitor.com', TRUE)
ON CONFLICT (username) DO NOTHING;
SQL
fi

echo ""
echo "Step 8: Restarting backend to reconnect..."
docker-compose restart backend

echo ""
echo "=========================================="
echo "✅ Database fix complete!"
echo "=========================================="
echo ""
echo "Services status:"
docker-compose ps

echo ""
echo "You can now login at:"
echo "  URL: http://74.48.129.112"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "If still having issues, check logs:"
echo "  docker-compose logs postgres"
echo "  docker-compose logs backend"
echo ""
