# 🔧 TROUBLESHOOTING - Domain Monitor

## 🔐 Login Issues (admin / admin123)

### ❌ "Incorrect username or password"

### ❌ "FATAL: database 'domainuser' does not exist"

Đây là 2 vấn đề phổ biến nhất. Có nhiều cách giải quyết:

---

## ⚡ Quick Fix (Recommended)

### Method 0: Database Fix (If you see database errors)

```bash
# Check postgres logs first
docker-compose logs postgres | tail -20

# If you see "database does not exist" or initialization errors:
./fix-database.sh
```

This will:
1. Stop all services
2. Delete old database volume
3. Recreate fresh database
4. Initialize with admin user
5. Restart services

**⚠️ WARNING**: This deletes all domains and scan data!

### Method 1: Automatic Reset Script

```bash
# Run the reset script
./reset-admin.sh
```

This will:
1. Delete old admin user
2. Create new admin with correct password hash
3. Verify the user was created
4. Show login credentials

**Then try login again at http://74.48.129.112**

---

### Method 2: Debug Script

```bash
# Run debug to see what's wrong
./debug-login.sh
```

This will check:
1. Services status
2. Database connection
3. Users table
4. Admin user exists
5. Backend logs
6. API endpoints
7. Try actual login

Based on output, it will tell you what's wrong.

---

## 🔍 Manual Troubleshooting

### Step 1: Check if services are running

```bash
docker-compose ps
```

Expected output:
```
domain-monitor-postgres   Up
domain-monitor-redis      Up  
domain-monitor-backend    Up
domain-monitor-scanner    Up
domain-monitor-nginx      Up
```

If any service is not "Up":
```bash
docker-compose up -d
```

---

### Step 2: Check database connection

```bash
docker-compose exec postgres psql -U domainuser -d domains -c "SELECT 1;"
```

Expected: `1` (one row)

If error:
```bash
# Restart PostgreSQL
docker-compose restart postgres
sleep 5
```

---

### Step 3: Check if users table exists

```bash
docker-compose exec postgres psql -U domainuser -d domains -c "\dt users"
```

Expected: Should show `users` table

If "relation does not exist":
```bash
# Database not initialized - Recreate
docker-compose down -v
docker-compose up -d
```

---

### Step 4: Check if admin user exists

```bash
docker-compose exec postgres psql -U domainuser -d domains << SQL
SELECT username, email, is_active, 
       length(password_hash) as hash_length,
       created_at 
FROM users 
WHERE username = 'admin';
SQL
```

**Expected output:**
```
 username |         email          | is_active | hash_length |         created_at         
----------+------------------------+-----------+-------------+----------------------------
 admin    | admin@domain-monitor.com | t         |          60 | 2024-11-25 10:00:00
```

**If no rows (admin doesn't exist):**
```bash
# Create admin user
docker-compose exec postgres psql -U domainuser -d domains << 'SQL'
INSERT INTO users (username, password_hash, email, is_active) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XnVx4L8sCYDS', 'admin@domain-monitor.com', TRUE)
ON CONFLICT (username) DO NOTHING;
SQL
```

**If admin exists but wrong password:**
```bash
# Reset password
docker-compose exec postgres psql -U domainuser -d domains << 'SQL'
UPDATE users 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XnVx4L8sCYDS',
    is_active = TRUE
WHERE username = 'admin';
SQL
```

---

### Step 5: Verify password hash

The correct bcrypt hash for password `admin123` is:
```
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XnVx4L8sCYDS
```

Check current hash:
```bash
docker-compose exec postgres psql -U domainuser -d domains << SQL
SELECT username, password_hash FROM users WHERE username = 'admin';
SQL
```

If different, update it:
```bash
docker-compose exec postgres psql -U domainuser -d domains << 'SQL'
UPDATE users 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5XnVx4L8sCYDS'
WHERE username = 'admin';
SQL
```

---

### Step 6: Check backend logs

```bash
docker-compose logs backend
```

Look for:
- ✅ "Connected to PostgreSQL and Redis" - Good
- ❌ "Connection refused" - Database issue
- ❌ "Authentication failed" - Wrong DB credentials

If backend has errors:
```bash
# Restart backend
docker-compose restart backend

# Watch logs
docker-compose logs -f backend
```

---

### Step 7: Test API directly

```bash
# Test health endpoint
curl http://74.48.129.112:8080/

# Expected: {"status":"ok","message":"Domain Monitoring API",...}
```

```bash
# Test login endpoint
curl -X POST http://74.48.129.112:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Expected: {"access_token":"...", "token_type":"bearer", ...}
# Error: {"detail":"Incorrect username or password"}
```

---

## 🗄️ Database Errors

### Error: "FATAL: database 'domainuser' does not exist"

**Root cause:** PostgreSQL healthcheck was looking for wrong database name.

**Quick fix:**
```bash
# Use the fix script
./fix-database.sh
```

**Manual fix:**
```bash
# Stop services
docker-compose down

# Remove old volume
docker volume rm domain-monitor_postgres_data

# Start fresh
docker-compose up -d

# Wait for init (important!)
sleep 30

# Verify
docker-compose exec postgres psql -U domainuser -d domains -c "SELECT 1;"
```

**Prevention:**
The `docker-compose.yml` has been fixed with correct healthcheck:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U domainuser -d domains"]
```

### Error: "relation users does not exist"

**Root cause:** init.sql not executed or failed.

**Fix:**
```bash
# Check if init.sql exists
ls -l database/init.sql

# Run it manually
docker-compose exec -T postgres psql -U domainuser -d domains < database/init.sql

# Verify tables
docker-compose exec postgres psql -U domainuser -d domains -c "\dt"
```

### Error: Connection timeout to database

**Fix:**
```bash
# Check postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart postgres

# Wait for it to be ready
sleep 10
```

---

## 🐛 Common Root Causes

### 1. Database not initialized

**Symptoms:**
- "relation users does not exist"
- No tables in database

**Fix:**
```bash
# Recreate everything
docker-compose down -v
docker-compose up -d

# Check logs
docker-compose logs postgres
```

---

### 2. Wrong SECRET_KEY

**Symptoms:**
- Login works but tokens don't validate
- "Could not validate credentials"

**Fix:**
```bash
# Check .env file
cat .env | grep SECRET_KEY

# Make sure it's set
echo "SECRET_KEY=your-secret-key-here" >> .env

# Restart backend
docker-compose restart backend
```

---

### 3. Backend not connecting to database

**Symptoms:**
- Backend logs show connection errors
- "could not connect to server"

**Check:**
```bash
# From backend container, try connecting
docker-compose exec backend sh -c 'python3 -c "
import asyncpg
import asyncio
asyncio.run(asyncpg.connect(\"postgresql://domainuser:domainpass123@postgres:5432/domains\"))
print(\"Connection OK\")
"'
```

**Fix:**
```bash
# Restart both services
docker-compose restart postgres backend
```

---

### 4. Frontend API URL wrong

**Check frontend files:**
```bash
# Check API URL in login.html
grep "API_BASE_URL" frontend/login.html

# Should be: const API_BASE_URL = 'http://74.48.129.112:8080/api';
```

If wrong, edit and fix:
```bash
nano frontend/login.html
# Change API_BASE_URL to: http://74.48.129.112:8080/api

# Restart nginx
docker-compose restart nginx
```

---

## 🧪 Test Password Hashing

Want to generate your own password hash?

```python
# In Python
import bcrypt

password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))

# Output: $2b$12$... (60 characters)
```

Or using the script:
```bash
cd scripts
python3 -c "
import bcrypt
password = input('Enter password: ')
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print('Hash:', hashed.decode('utf-8'))
"
```

---

## 📋 Complete Reset Procedure

If nothing works, do a complete reset:

```bash
# 1. Stop everything
docker-compose down -v

# 2. Remove all data (WARNING: This deletes all domains and scans!)
docker volume rm $(docker volume ls -q | grep domain-monitor) 2>/dev/null

# 3. Start fresh
docker-compose up -d

# 4. Wait for initialization
sleep 10

# 5. Check if admin exists
docker-compose exec postgres psql -U domainuser -d domains -c "SELECT * FROM users;"

# 6. If no admin, create one
./reset-admin.sh

# 7. Try login
# URL: http://74.48.129.112
# Username: admin
# Password: admin123
```

---

## 🎯 After Successful Login

Once you can login:

1. **Change password immediately:**
   - Go to user profile
   - Click "Change Password"
   - Use a strong password

2. **Create additional users if needed:**
   ```bash
   cd scripts
   python3 create_admin.py
   ```

3. **Test key features:**
   - Add a test domain
   - Trigger a scan
   - Check results
   - Export CSV

---

## 📞 Still Having Issues?

### Check all logs:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs postgres
docker-compose logs nginx
```

### Get service info:

```bash
# Container status
docker-compose ps

# Network info
docker network inspect domain-monitor_domain-monitor

# Volume info
docker volume ls | grep domain-monitor
```

### Test each component:

```bash
# PostgreSQL
docker-compose exec postgres psql -U domainuser -d domains -c "SELECT COUNT(*) FROM users;"

# Redis
docker-compose exec redis redis-cli PING

# Backend API
curl http://74.48.129.112:8080/health

# Nginx
curl -I http://74.48.129.112
```

---

## ✅ Success Indicators

You should see:

1. **Services running:**
   ```bash
   $ docker-compose ps
   All containers show "Up"
   ```

2. **Admin user exists:**
   ```bash
   $ ./debug-login.sh
   Admin user count: 1
   ✅ Admin user exists
   ```

3. **Login works:**
   ```bash
   $ curl -X POST http://74.48.129.112:8080/api/auth/login ...
   {"access_token":"...", "token_type":"bearer"}
   ```

4. **Dashboard accessible:**
   ```
   http://74.48.129.112 → Shows login page
   Login with admin/admin123 → Shows dashboard
   ```

---

## 🎉 Problem Solved?

If you successfully logged in:
- ✅ Change your password
- ✅ Add test domains
- ✅ Trigger a scan
- ✅ Explore the dashboard

If still having issues:
- Run `./debug-login.sh` and share output
- Check logs: `docker-compose logs`
- Verify IP and port settings

---

**Scripts created to help:**
- `reset-admin.sh` - Quick password reset
- `debug-login.sh` - Comprehensive debugging
- `scripts/create_admin.py` - Interactive admin creation

**Happy monitoring! 🚀**
