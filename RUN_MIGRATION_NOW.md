# 🚨 RUN MIGRATION NOW!

## ❌ Current Error

```
asyncpg.exceptions.UndefinedTableError: relation "users" does not exist
```

**Problem:** Auth tables haven't been created yet. You need to run the migration!

---

## ✅ Solution: Run Migration

### Option 1: Using PowerShell (Windows)

```powershell
# Open PowerShell in project directory
cd "d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1"

# Run migration
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql
```

### Option 2: Using Git Bash / WSL

```bash
cd /d/VNNIC/4.\ CA\ NHAN/Freelancer/Namestar/Monitoring/ssl-monitoring-v1

docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql
```

### Option 3: Using CMD (Windows)

```cmd
cd d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1

type database\auth_migration.sql | docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor
```

### Option 4: Manual via Docker

```bash
# Copy SQL file into container
docker cp database/auth_migration.sql ssl-monitoring-postgres:/tmp/

# Execute SQL
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -f /tmp/auth_migration.sql
```

---

## 🔍 Verify Migration Success

After running migration, check if tables were created:

```bash
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "\dt"
```

**Expected output:**
```
             List of relations
 Schema |       Name        | Type  |  Owner
--------+-------------------+-------+---------
 public | audit_logs        | table | ssluser
 public | domains           | table | ssluser
 public | permissions       | table | ssluser
 public | role_permissions  | table | ssluser
 public | roles             | table | ssluser
 public | sessions          | table | ssluser
 public | ssl_scan_results  | table | ssluser
 public | users             | table | ssluser
```

---

## 🧪 Test Login After Migration

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"Admin@123\"}"
```

**Expected response:**
```json
{
  "token": "some-long-token",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@sslmonitor.local",
    "role_name": "admin",
    ...
  },
  "expires_at": "2025-01-30T..."
}
```

---

## 🌐 Test Frontend

1. Open browser: http://localhost:8888
2. Should redirect to login page
3. Login with: `admin` / `Admin@123`
4. Should successfully enter dashboard

---

## ⚠️ If Migration Fails

### Error: "relation already exists"

Tables already created - this is OK! You can ignore this error.

### Error: "password authentication failed"

Check database credentials:
```bash
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT 1"
```

If fails, check `docker-compose.yml` for correct password.

### Error: "could not connect to server"

PostgreSQL not running:
```bash
docker compose up -d postgres
sleep 5
# Then retry migration
```

---

## 📝 Quick Summary

**Run this ONE command (PowerShell on Windows):**

```powershell
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql
```

**Then test:**
- Frontend: http://localhost:8888 → login page
- Login: admin / Admin@123
- Should work! ✅

---

## 🎯 After Migration

Your system will have:
- ✅ 6 new auth tables (users, roles, permissions, etc.)
- ✅ Default admin user (admin/Admin@123)
- ✅ 3 roles with 15 permissions
- ✅ Full authentication system working

**Run the migration NOW and your system will work!** 🚀
