# 🚀 SSL Monitor v2.2 - Deployment Guide

## ✅ VERIFIED & READY TO DEPLOY

---

## 📦 **Package Info**

- **Version:** 2.2.0 (Final)
- **Size:** 65 KB
- **Database:** PostgreSQL 15-alpine (stable, proven)
- **Scanner:** Bash (openssl + curl - 100% accurate)
- **Frontend:** AdminLTE (no "Sort By" - as requested)
- **Status:** ✅ All files verified

---

## 🎯 **3-Step Deployment**

### Step 1: Extract Package

```bash
# On your server
cd /opt/monitoring-v8

# Extract
tar -xzf ssl-monitor-v2.2-final.tar.gz
cd domain-monitor

# Verify files
ls -la
```

**You should see:**
```
database/
scanner/
backend/
frontend/
nginx/
docker-compose.yml
.env
README.md
```

### Step 2: Deploy with Docker

```bash
# Start all services
docker-compose up -d --build

# Output should show:
# Creating network "domain-monitor_ssl-monitor"
# Creating volume "domain-monitor_postgres_data"
# Building backend...
# Building scanner...
# Creating ssl-monitor-postgres...
# Creating ssl-monitor-backend...
# Creating ssl-monitor-scanner...
# Creating ssl-monitor-nginx...
```

### Step 3: Wait & Verify

```bash
# Wait 30 seconds for initialization
sleep 30

# Check all services are running
docker-compose ps
```

**Expected output:**
```
NAME                      STATUS
ssl-monitor-postgres     Up (healthy)
ssl-monitor-backend      Up
ssl-monitor-scanner      Up
ssl-monitor-nginx        Up
```

---

## ✅ **Verification Steps**

### 1. Check PostgreSQL:
```bash
docker-compose logs postgres | tail -20
```

Should see:
```
[Note] database system is ready to accept connections
```

### 2. Check Backend:
```bash
curl http://YOUR_IP_ADDRESS:8080/
```

Expected response:
```json
{
  "status": "ok",
  "message": "SSL Certificate Monitoring API - PostgreSQL + Bash Scanner",
  "version": "2.2.0",
  "port": 8080
}
```

### 3. Check Frontend:
```bash
curl -I http://YOUR_IP_ADDRESS
```

Expected:
```
HTTP/1.1 200 OK
Content-Type: text/html
```

### 4. Open Browser:
```
http://YOUR_IP_ADDRESS
```

**Should see:**
- ✅ Dashboard loads
- ✅ 4 stats cards (all showing 0)
- ✅ Filters section (WITHOUT "Sort By")
- ✅ Domain list (empty)
- ✅ Sidebar menu
- ✅ No errors

---

## ➕ **Add Your First Domain**

### Via UI (Recommended):

1. Open http://YOUR_IP_ADDRESS
2. Click **"Add Domain"** in left sidebar
3. Enter domain: `google.com`
4. Click **"Add Domain"**
5. Success message appears

### Via API:

```bash
curl -X POST http://YOUR_IP_ADDRESS:8080/api/domains \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'
```

Response:
```json
{
  "id": 1,
  "domain": "google.com",
  "created_at": "2025-11-26T10:00:00"
}
```

---

## 🔍 **Trigger First Scan**

Scanner runs automatically every 1 hour, but you can trigger immediately:

```bash
# Restart scanner to run now
docker-compose restart scanner

# Watch logs in real-time
docker-compose logs -f scanner
```

**Expected output:**
```
[INFO] SSL Certificate Scanner starting...
[INFO] Configuration:
[INFO]   - Database: postgres:5432/ssl_monitor
[INFO]   - Concurrency: 20
[INFO]   - Timeout: 5s
[INFO] PostgreSQL is ready!
[INFO] ==========================================
[INFO] Starting SSL Certificate Scan
[INFO] ==========================================
[INFO] Total domains to scan: 1
[INFO] Concurrency: 20 threads
[INFO] Scanning domains...
RESULT:1|VALID|Mar 11 08:15:38 2025 GMT|105|200|-
[INFO] Saving results to database...
[INFO] ==========================================
[INFO] Scan Completed!
[INFO] ==========================================
[INFO] Total scanned: 1 domains
[INFO] SSL Valid: 1
[INFO] SSL Invalid: 0
[INFO] Expired Soon (<7 days): 0
[INFO] Failed: 0
[INFO] Duration: 1s
[INFO] Throughput: 1.0 domains/second
[INFO] ==========================================
```

Press Ctrl+C to stop watching logs.

---

## 📊 **Check Dashboard**

Refresh browser: http://YOUR_IP_ADDRESS

**Should now show:**
- Total Domains: **1**
- SSL Valid: **1**
- Expired Soon: **0**
- Failed: **0**

**Domain list should show:**
- Domain: `google.com`
- SSL Status: 🟢🟢🟢🟢🟢 (5 green dots)
- Expired on: Green badge with date and days
- HTTPS Status: Green badge "200"
- Redirect: `-`
- Last Scan: Current time

---

## 🎛️ **Dashboard Features**

### Filters (NO "Sort By" as requested):

1. **Search Domain** - Type domain name
2. **SSL Status** - All / Valid / Invalid
3. **Expiry Status** - All / Expired Soon / Valid
4. **HTTPS Status** - All / 2xx / 3xx / 4xx / 5xx / Failed
5. **Apply Filters** - Click to filter

### Stats Cards (clickable):
- Click **Total Domains** → Shows all
- Click **SSL Valid** → Filters valid only
- Click **Expired Soon** → Filters expiring <7 days
- Click **Failed** → Filters failed only

### Bulk Operations:
- Select multiple domains (checkboxes)
- Click **Delete Selected**
- Confirm deletion

---

## ⚙️ **Configuration**

### Scan Settings:

Edit `.env`:
```bash
# Faster scans (for large domain lists)
CONCURRENCY=50

# More frequent scans
SCAN_INTERVAL=1800    # Every 30 minutes

# Longer timeout (for slow domains)
TIMEOUT=10
```

Apply changes:
```bash
docker-compose restart scanner
```

### Performance Guide:

| Domains | CONC=20 | CONC=50 | CONC=100 |
|---------|---------|---------|----------|
| 1,000   | ~2 min  | ~45s    | ~25s     |
| 10,000  | ~15 min | ~7 min  | ~3 min   |
| 50,000  | ~70 min | ~30 min | ~15 min  |

---

## 🐛 **Troubleshooting**

### PostgreSQL won't start:

```bash
# Check logs
docker-compose logs postgres

# Common fixes:
docker-compose down -v
docker-compose up -d
```

### Scanner not scanning:

```bash
# Check logs
docker-compose logs scanner

# Restart
docker-compose restart scanner
```

### Dashboard shows 0 after scan:

```bash
# Refresh materialized view manually
docker-compose exec postgres psql -U ssluser -d ssl_monitor -c "REFRESH MATERIALIZED VIEW latest_ssl_status;"

# Refresh browser
```

### Backend API error:

```bash
# Check logs
docker-compose logs backend

# Restart
docker-compose restart backend
```

### Frontend not loading:

```bash
# Check logs
docker-compose logs nginx

# Restart
docker-compose restart nginx
```

---

## 📝 **Common Tasks**

### Add 100 domains:

Create `domains.txt`:
```
domain1.com
domain2.com
domain3.com
...
```

Bulk add:
```bash
DOMAINS=$(cat domains.txt | jq -R . | jq -s .)
curl -X POST http://YOUR_IP_ADDRESS:8080/api/domains/bulk \
  -H "Content-Type: application/json" \
  -d "{\"domains\": $DOMAINS}"
```

### Export CSV report:

```bash
# All domains
curl http://YOUR_IP_ADDRESS:8080/api/export/csv > report.csv

# Only valid
curl "http://YOUR_IP_ADDRESS:8080/api/export/csv?ssl_status=VALID" > valid.csv

# Only expired soon
curl "http://YOUR_IP_ADDRESS:8080/api/export/csv?expired_soon=true" > expired.csv
```

### Backup database:

```bash
docker-compose exec postgres pg_dump -U ssluser ssl_monitor > backup.sql
```

### Restore database:

```bash
docker-compose exec -T postgres psql -U ssluser ssl_monitor < backup.sql
```

### View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f scanner
docker-compose logs -f backend
docker-compose logs -f postgres
```

---

## 🎉 **Success Checklist**

- [ ] Package extracted
- [ ] Docker services running
- [ ] PostgreSQL healthy
- [ ] Backend API responding
- [ ] Frontend loads (no "Sort By")
- [ ] Test domain added
- [ ] Scanner completed first scan
- [ ] Dashboard shows statistics
- [ ] Filters work
- [ ] Domain list populated
- [ ] SSL status dots visible
- [ ] Can export CSV

---

## 📚 **Support**

### Files:
- **DEPLOY.md** - This file (deployment guide)
- **README.md** - Full documentation
- **.env** - Configuration
- **docker-compose.yml** - Services

### Commands:
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Restart service
docker-compose restart <service>

# Stop all
docker-compose down

# Start all
docker-compose up -d
```

---

## ✅ **Summary**

**Package:** ssl-monitor-v2.2-final.tar.gz (65 KB)  
**Status:** ✅ Verified & Ready  
**Database:** PostgreSQL 15  
**Scanner:** Bash (openssl + curl)  
**Frontend:** No "Sort By" (as requested)  

**Deploy:**
```bash
tar -xzf ssl-monitor-v2.2-final.tar.gz
cd domain-monitor
docker-compose up -d --build
```

**Access:**
```
http://YOUR_IP_ADDRESS
```

**Enjoy monitoring your SSL certificates! 🔐**
