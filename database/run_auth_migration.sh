#!/bin/bash

# Run authentication migration
echo "Running authentication migration..."

PGPASSWORD="SSL@Pass123" psql -h localhost -p 5432 -U ssluser -d ssl_monitor -f auth_migration.sql

if [ $? -eq 0 ]; then
    echo "✅ Authentication migration completed successfully!"
    echo ""
    echo "Default admin credentials:"
    echo "  Username: admin"
    echo "  Password: Admin@123"
    echo ""
    echo "⚠️  IMPORTANT: Change the default password after first login!"
else
    echo "❌ Migration failed!"
    exit 1
fi
