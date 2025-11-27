# 🧪 Quick Test Guide - After Deployment

## After `docker-compose up -d --build`

### 1. Wait & Check Services (30 seconds)

```bash
sleep 30
docker-compose ps
```

**Expected:**
```
NAME                      STATUS
ssl-monitor-postgres     Up (healthy)
ssl-monitor-backend      Up (healthy)  ← Should show "healthy"
ssl-monitor-scanner      Up
ssl-monitor-nginx        Up
```

### 2. Check Backend Logs

```bash
docker-compose logs backend | tail -20
```

**Should see:**
```
Starting application...
Connecting to PostgreSQL at postgres:5432/ssl_monitor
✅ Successfully connected to PostgreSQL
FastAPI application started
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Should NOT see:**
```
❌ Failed to connect
Connection refused
ImportError
ModuleNotFoundError
```

### 3. Test Backend API

```bash
curl http://YOUR_IP_ADDRESS:8080/
```

**Expected response:**
```json
{
  "status": "ok",
  "message": "SSL Certificate Monitoring API - PostgreSQL + Bash Scanner",
  "version": "2.2.0",
  "port": 8080,
  "database": "postgres:5432/ssl_monitor"
}
```

### 4. Test Health Endpoint

```bash
curl http://YOUR_IP_ADDRESS:8080/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "ok"
}
```

### 5. Test Dashboard Summary

```bash
curl http://YOUR_IP_ADDRESS:8080/api/dashboard/summary
```

**Expected:**
```json
{
  "total_domains": 0,
  "ssl_valid_count": 0,
  "expired_soon_count": 0,
  "failed_count": 0,
  "last_scan_time": null
}
```

### 6. Test Frontend

```bash
curl -I http://YOUR_IP_ADDRESS
```

**Expected:**
```
HTTP/1.1 200 OK
Content-Type: text/html
```

### 7. Open Browser

```
http://YOUR_IP_ADDRESS
```

**Should see:**
- ✅ Dashboard loads
- ✅ 4 stats cards (all 0)
- ✅ Filters (no "Sort By")
- ✅ Empty domain list
- ✅ No JavaScript errors in console (F12)

---

## If Backend Fails

### Scenario 1: "Connection refused" to PostgreSQL

```bash
# Check PostgreSQL
docker-compose logs postgres | tail -20

# Should see:
# database system is ready to accept connections

# If not ready, wait longer
sleep 30

# Restart backend
docker-compose restart backend
```

### Scenario 2: ImportError or ModuleNotFoundError

```bash
# Check installed packages
docker-compose exec backend pip list

# Should show:
# fastapi, uvicorn, asyncpg, pydantic, requests

# If missing, rebuild
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Scenario 3: Backend exits immediately

```bash
# Check full logs
docker-compose logs backend

# Look for Python errors
# Common issues:
# - Syntax error in main.py
# - Missing environment variables
# - Port already in use

# Check if port 8080 is available
netstat -tlnp | grep 8080

# If port is used, kill the process or change port in docker-compose.yml
```

### Scenario 4: 503 Service Unavailable

```bash
# Backend is running but can't connect to database

# Test database connection
docker-compose exec postgres psql -U ssluser -d ssl_monitor -c "SELECT 1"

# If database error, check credentials in .env
cat .env | grep DB_

# Restart both services
docker-compose restart postgres backend
```

---

## Add Test Domain

Once all tests pass:

```bash
# Add test domain
curl -X POST http://YOUR_IP_ADDRESS:8080/api/domains \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'

# Trigger scan
docker-compose restart scanner

# Watch scan
docker-compose logs -f scanner

# Expected:
# [INFO] Scanning domains...
# RESULT:1|VALID|Mar 11 08:15:38 2025 GMT|105|200|-
# [INFO] Scan Completed!
# [INFO] SSL Valid: 1
```

---

## Success Indicators

✅ All services "Up"  
✅ Backend logs show "Successfully connected"  
✅ API returns JSON responses  
✅ Frontend loads without errors  
✅ Can add domains  
✅ Scanner completes successfully  
✅ Dashboard updates with data  

---

## Common Errors & Quick Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| Connection refused | PostgreSQL not ready | Wait 30s, restart backend |
| ImportError | Missing package | Rebuild backend |
| Port in use | Another service on 8080 | Change port or kill process |
| 503 Error | Database connection failed | Check .env, restart services |
| Empty response | Nginx misconfigured | Check nginx logs |

---

**If all tests pass → System is working! 🎉**

**If any test fails → Check logs and use fixes above**
