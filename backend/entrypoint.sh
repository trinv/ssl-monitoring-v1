#!/bin/bash
set -e

echo "=========================================="
echo "SSL Monitor Backend Starting..."
echo "=========================================="
echo ""

echo "Configuration:"
echo "  DB_HOST: ${DB_HOST:-postgres}"
echo "  DB_PORT: ${DB_PORT:-5432}"
echo "  DB_NAME: ${DB_NAME:-ssl_monitor}"
echo "  DB_USER: ${DB_USER:-ssluser}"
echo ""

echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1" > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    echo "⏳ Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

echo ""
echo "Starting uvicorn server..."
echo "=========================================="
exec uvicorn main:app --host 0.0.0.0 --port 8080 --log-level info
