# 🔐 SSL Certificate Monitor v2.2 - Production Ready

## ✅ Stable & Accurate - PostgreSQL + Bash Scanner

---

## 📦 **What's Included**

- ✅ **PostgreSQL 15** - Reliable database (proven stable)
- ✅ **Bash Scanner** - Uses openssl + curl (100% accurate)
- ✅ **FastAPI Backend** - Python async API
- ✅ **AdminLTE Dashboard** - Complete UI (no "Sort By")
- ✅ **Docker Compose** - One-command deployment

---

## 🚀 **Quick Deploy (3 steps)**

### Step 1: Extract
```bash
tar -xzf ssl-monitor-v2.2-final.tar.gz
cd domain-monitor
```

### Step 2: Deploy
```bash
docker-compose up -d --build
```

### Step 3: Wait & Access
```bash
# Wait 30 seconds for services to start
sleep 30

# Access dashboard
http://YOUR_IP_ADDRESS
```

---

## 📊 **Dashboard Features**

### Stats Cards:
- **Total Domains** - All monitored domains
- **SSL Valid** - Domains with valid SSL certificates
- **Expired Soon** - SSL expires in < 7 days
- **Failed** - Invalid SSL or no HTTPS response

### Filters (no Sort By):
- **Search Domain** - Search by domain name
- **SSL Status** - Filter by Valid/Invalid
- **Expiry Status** - Filter by expired soon
- **HTTPS Status** - Filter by HTTP codes (2xx, 3xx, 4xx, 5xx)
- **Apply Filters** - Button to apply filters

### Domain List:
- Domain name
- SSL Status History (5 dots: 🟢 Valid / 🔴 Invalid)
- Expiry Date (🔴 < 7 days / 🟢 >= 7 days)
- HTTPS Status (color-coded)
- Redirect URL (if any)
- Last Scan time
- Delete button

---

## ➕ **Add Domains**

### Via UI:
1. Click **"Add Domain"** in sidebar
2. Enter domain: `google.com`
3. Click **"Add Domain"**

### Via API:
```bash
curl -X POST http://YOUR_IP_ADDRESS:8080/api/domains \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'
```

### Bulk Add:
```bash
# Prepare domains.txt
cat > domains.txt << 'DOMAINS'
google.com
facebook.com
github.com
DOMAINS

# Convert to JSON and add
DOMAINS=$(cat domains.txt | jq -R . | jq -s .)
curl -X POST http://YOUR_IP_ADDRESS:8080/api/domains/bulk \
  -H "Content-Type: application/json" \
  -d "{\"domains\": $DOMAINS}"
```

---

## 🔍 **How Scanner Works**

### Bash Script Logic:
```bash
# 1. Check SSL certificate
CERT_INFO=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN")

# 2. Get expiry date
EXPIRY=$(echo "$CERT_INFO" | openssl x509 -noout -enddate | cut -d= -f2)

# 3. Check HTTPS status
CURL_OUTPUT=$(curl -Ik --max-time 5 -L "https://$DOMAIN")
HTTPS_STATUS=$(echo "$CURL_OUTPUT" | grep -m1 HTTP | awk '{print $2}')

# 4. Save to PostgreSQL
psql -c "INSERT INTO ssl_scan_results (...) VALUES (...);"
```

**Same as check_ssl_bulk.sh - 100% accurate!**

---

## ⚙️ **Configuration**

### Default Settings (.env):
```bash
# Database
DB_PASSWORD=SSL@Pass123

# Scanner
CONCURRENCY=20          # Parallel domains
SCAN_INTERVAL=3600      # Scan every 1 hour
TIMEOUT=5               # Timeout per domain
```

### Adjust Performance:
```bash
# For faster scans (more domains)
CONCURRENCY=50
SCAN_INTERVAL=7200

# For more frequent scans
SCAN_INTERVAL=1800      # Every 30 minutes
```

After changes:
```bash
docker-compose restart scanner
```

---

## 🧪 **Verify Deployment**

### 1. Check Services:
```bash
docker-compose ps
```

Expected:
```
ssl-monitor-postgres   Up (healthy)
ssl-monitor-backend    Up
ssl-monitor-scanner    Up
ssl-monitor-nginx      Up
```

### 2. Check Backend:
```bash
curl http://YOUR_IP_ADDRESS:8080/
```

Expected:
```json
{
  "status": "ok",
  "message": "SSL Certificate Monitoring API - PostgreSQL + Bash Scanner",
  "version": "2.2.0"
}
```

### 3. Check Frontend:
```bash
curl -I http://YOUR_IP_ADDRESS
```

Expected: `HTTP/1.1 200 OK`

### 4. Add Test Domain:
```bash
curl -X POST http://YOUR_IP_ADDRESS:8080/api/domains \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'
```

### 5. Trigger Scan:
```bash
docker-compose restart scanner
docker-compose logs -f scanner
```

Expected output:
```
[INFO] Starting SSL Certificate Scan
[INFO] Total domains to scan: 1
[INFO] Scanning domains...
RESULT:1|VALID|Mar 11 08:15:38 2025 GMT|105|200|-
[INFO] Scan Completed!
[INFO] SSL Valid: 1
```

### 6. Check Dashboard:
Open: http://YOUR_IP_ADDRESS

Should show:
- Total Domains: 1
- SSL Valid: 1
- Domain list with google.com

---

## 🐛 **Troubleshooting**

### PostgreSQL not starting:
```bash
docker-compose logs postgres
docker-compose restart postgres
```

### Scanner not running:
```bash
docker-compose logs scanner
docker-compose restart scanner
```

### Backend error:
```bash
docker-compose logs backend
docker-compose restart backend
```

### Frontend 403/404:
```bash
docker-compose logs nginx
docker-compose restart nginx
```

### Dashboard shows 0:
```bash
# Check if domains exist
docker-compose exec postgres psql -U ssluser -d ssl_monitor -c "SELECT COUNT(*) FROM domains;"

# Refresh materialized view
docker-compose exec postgres psql -U ssluser -d ssl_monitor -c "REFRESH MATERIALIZED VIEW latest_ssl_status;"
```

---

## 📂 **Package Structure**

```
domain-monitor/
├── database/
│   └── init.sql              ← PostgreSQL schema
├── scanner/
│   ├── scanner.sh           ← Bash scanner (openssl + curl)
│   └── Dockerfile
├── backend/
│   ├── main.py              ← FastAPI API
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── index.html           ← Complete UI (no "Sort By")
├── nginx/
│   └── nginx.conf
├── docker-compose.yml       ← PostgreSQL + services
├── .env                     ← Configuration
└── README.md                ← This file
```

---

## 🎉 **Summary**

**Version:** 2.2.0 (Final)  
**Database:** PostgreSQL 15  
**Scanner:** Bash (openssl + curl)  
**Frontend:** AdminLTE (no "Sort By")  
**Status:** ✅ Production Ready  

**Key Features:**
- SSL certificate validation
- Expiry date tracking
- HTTPS status checking
- Redirect detection
- Historical tracking (5 scans)
- Advanced filtering (4 filters)
- Bulk operations
- CSV export

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

**Ready to monitor your SSL certificates! 🔐**
