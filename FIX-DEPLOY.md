# 🔧 Fixed Deployment - v2.1

## Issues Fixed:
1. ✅ Backend CORS: "Host not allowed" → Fixed
2. ✅ Nginx 403 Forbidden → Fixed
3. ✅ Frontend serving → Fixed

---

## Deploy Fixed Version

### If you already deployed:

```bash
cd /opt/monitoring-v8/domain-monitor

# Stop services
docker-compose down

# Backup old files
cp backend/main.py backend/main.py.old
cp nginx/nginx.conf nginx/nginx.conf.old

# Extract new version over existing
cd /opt/monitoring-v8
tar -xzf domain-monitor-mariadb-v2.1-fixed.tar.gz

# Restart
cd domain-monitor
docker-compose up -d --build
```

### Fresh deployment:

```bash
# Extract
tar -xzf domain-monitor-mariadb-v2.1-fixed.tar.gz
cd domain-monitor

# Deploy
docker-compose up -d --build

# Wait
sleep 30
```

---

## Verify Fix

### 1. Check Services:
```bash
docker-compose ps
```

All should be **Up (healthy)**.

### 2. Check Backend API:
```bash
curl http://74.48.129.112:8080/

# Should return JSON:
# {
#   "status": "ok",
#   "message": "SSL Certificate Monitoring API...",
#   "version": "2.1.0"
# }
```

### 3. Check Frontend:
```bash
curl -I http://74.48.129.112

# Should return:
# HTTP/1.1 200 OK
```

### 4. Check Dashboard:
Open browser: http://74.48.129.112

Should see:
- ✅ Dashboard loads
- ✅ Stats cards visible
- ✅ "No domains found" message (until you add domains)

---

## Add Test Domain

```bash
curl -X POST http://74.48.129.112:8080/api/domains \
  -H "Content-Type: application/json" \
  -d '{"domain": "google.com"}'

# Wait for scanner (or restart it)
docker-compose restart scanner

# Watch scanner logs
docker-compose logs -f scanner
```

---

## What Was Fixed

### 1. Backend CORS (main.py):
```python
# Before:
allow_credentials=True  # Doesn't work with allow_origins=["*"]

# After:
allow_credentials=False  # Works with allow_origins=["*"]
```

### 2. Nginx Config:
```nginx
# Added:
include /etc/nginx/mime.types;  # For proper content types

# Fixed:
location / {
    root /usr/share/nginx/html;
    index index.html;              # Serve index.html
    try_files $uri $uri/ /index.html;
}
```

---

## Expected Result

After fix:
- ✅ Backend API accessible: http://74.48.129.112:8080
- ✅ Frontend loads: http://74.48.129.112
- ✅ Dashboard shows UI
- ✅ Can add domains via UI
- ✅ Scanner runs and saves results
- ✅ Dashboard updates with stats

---

## If Still Have Issues

### Backend not responding:
```bash
docker-compose logs backend
docker-compose restart backend
```

### Frontend 403:
```bash
docker-compose logs nginx
docker-compose restart nginx
```

### Scanner not working:
```bash
docker-compose logs scanner
docker-compose restart scanner
```

### Database connection error:
```bash
docker-compose logs mariadb

# Check connection
docker-compose exec mariadb mysql -ussluser -pSSL@Pass123 ssl_monitor -e "SELECT 1;"
```

---

## Package Files

- **domain-monitor-mariadb-v2.1-fixed.tar.gz** (65 KB)
- Fixed: backend/main.py, nginx/nginx.conf
- Everything else: same as v2.1

---

**Deploy and enjoy! 🔐**
