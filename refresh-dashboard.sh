#!/bin/bash
# Refresh Dashboard Data
# Use this if dashboard shows 0 but you have domains

echo "=========================================="
echo " Domain Monitor - Refresh Dashboard"
echo "=========================================="
echo ""

echo "Step 1: Checking database connection..."
if ! docker-compose exec -T postgres psql -U domainuser -d domains -c "SELECT 1;" > /dev/null 2>&1; then
    echo "❌ Cannot connect to database!"
    exit 1
fi
echo "✅ Database OK"

echo ""
echo "Step 2: Checking domains count..."
DOMAIN_COUNT=$(docker-compose exec -T postgres psql -U domainuser -d domains -t -c "SELECT COUNT(*) FROM domains;" | tr -d ' ')
echo "Found $DOMAIN_COUNT domains in database"

if [ "$DOMAIN_COUNT" -eq "0" ]; then
    echo "⚠️  No domains in database. Please add domains first."
    exit 0
fi

echo ""
echo "Step 3: Checking scan results..."
SCAN_COUNT=$(docker-compose exec -T postgres psql -U domainuser -d domains -t -c "SELECT COUNT(*) FROM scan_results;" | tr -d ' ')
echo "Found $SCAN_COUNT scan results"

if [ "$SCAN_COUNT" -eq "0" ]; then
    echo "⚠️  No scan results yet. Domains need to be scanned first."
    echo ""
    echo "To scan domains:"
    echo "  1. Wait for auto-scan (every 1 hour by default)"
    echo "  2. Or restart scanner: docker-compose restart scanner"
    echo "  3. Check scanner logs: docker-compose logs -f scanner"
    exit 0
fi

echo ""
echo "Step 4: Refreshing materialized view..."
docker-compose exec -T postgres psql -U domainuser -d domains << 'SQL'
REFRESH MATERIALIZED VIEW CONCURRENTLY latest_domain_status;
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'is_for_sale') as for_sale,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status = 'other') as other
FROM latest_domain_status;
SQL

echo ""
echo "Step 5: Restarting backend to clear any cache..."
docker-compose restart backend
sleep 3

echo ""
echo "=========================================="
echo "✅ Dashboard refreshed!"
echo "=========================================="
echo ""
echo "Please refresh your browser: http://74.48.129.112"
echo ""
echo "If still showing 0:"
echo "  1. Check scanner is running: docker-compose ps scanner"
echo "  2. View scanner logs: docker-compose logs -f scanner"
echo "  3. Manually trigger scan: docker-compose restart scanner"
echo ""
