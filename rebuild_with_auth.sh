#!/bin/bash

echo "=========================================="
echo "Rebuilding SSL Monitor with Authentication"
echo "=========================================="

# Stop all services
echo ""
echo "📦 Stopping all services..."
docker compose down

# Rebuild backend with auth module
echo ""
echo "🔨 Rebuilding backend image..."
docker compose build backend

# Start all services
echo ""
echo "🚀 Starting all services..."
docker compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migration
echo ""
echo "💾 Running authentication migration..."
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Authentication system deployed successfully!"
    echo "=========================================="
    echo ""
    echo "📝 Next steps:"
    echo "1. Access your application at http://localhost:8888"
    echo "2. You will be redirected to login page"
    echo "3. Login with: admin / Admin@123"
    echo ""
    echo "📊 Check logs:"
    echo "   docker logs ssl-monitor-backend"
    echo "   docker logs ssl-monitor-postgres"
    echo ""
else
    echo ""
    echo "❌ Migration failed! Check the error above."
    echo "You can manually run: docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql"
fi
