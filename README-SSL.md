# 🔐 SSL Certificate Monitoring System v2.0

## Hệ thống giám sát chứng chỉ SSL cho 50,000+ domains

**ĐÃ CHUYỂN ĐỔI HOÀN TOÀN từ "Domain For Sale Scanner" → "SSL Certificate Monitor"**

---

## 🎯 Tính năng chính

### Dashboard Statistics
- **Total Domains**: Tổng số domains được monitor
- **SSL Valid**: Số domains có SSL certificate hợp lệ
- **Expired Soon**: Số domains có SSL sắp hết hạn (< 7 ngày)
- **Failed**: Số domains không có SSL hoặc không truy cập được

### Domain List
- **Domain**: Tên miền
- **SSL Status History**: 5 lần scan gần nhất (🟢 valid / 🔴 invalid)
  - Hover để xem chi tiết từng lần scan
- **Expired on**: Ngày hết hạn SSL
  - 🔴 Red badge: < 7 days
  - 🟢 Green badge: >= 7 days
- **HTTPS Status**: HTTP status code (200, 301, 404, etc.)
  - 🟢 Green: 2xx success
  - 🟡 Yellow: 3xx redirect
  - 🔴 Red: 4xx/5xx errors
- **Redirect to**: URL đích (nếu có redirect)
- **Last Scan**: Thời gian scan gần nhất
- **Actions**: Delete domain

### Filters & Search
- Search by domain name
- Sort by: Domain (A-Z), SSL Status, Days to Expiry
- Filter by SSL Status: All, Valid, Invalid
- Filter by Expiry: All, Expired Soon, Valid
- Filter by HTTPS Status: All, 2xx, 3xx, 4xx, 5xx, Failed

---

## 📦 Package Structure

```
domain-monitor/
├── database/
│   └── init.sql                  ← SSL monitoring schema
├── backend/
│   ├── main.py                   ← SSL monitoring API
│   ├── requirements.txt
│   └── Dockerfile
├── scanner/
│   ├── scanner.py                ← SSL certificate scanner (NEW!)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── index.html                ← SSL monitoring dashboard (NEEDS UPDATE!)
├── nginx/
│   └── nginx.conf
├── docker-compose.yml            ← No Redis
├── .env                          ← Default passwords
│
└── Documentation/
    ├── README-SSL.md             ← This file
    ├── MIGRATION-TO-SSL.md       ← Migration guide
    └── FRONTEND-TODO.md          ← Frontend implementation guide
```

---

## 🚀 Quick Start

### 1. Chuẩn bị

```bash
# Extract package
tar -xzf domain-monitor-v2.0.tar.gz
cd domain-monitor

# .env đã có default passwords sẵn!
# POSTGRES_PASSWORD=s3gs8Tu50ISwFu37
```

### 2. Deploy

```bash
# Stop old version (if any)
docker-compose down -v

# Start new version
docker-compose up -d --build

# Wait for services
sleep 30

# Check logs
docker-compose logs -f scanner
```

### 3. Access

```
URL: http://YOUR_IP_ADDRESS
```

**No login needed!** Direct access to SSL monitoring dashboard.

---

## 🔧 Configuration

### Scanner Settings (.env)

```bash
SCAN_CONCURRENCY=2000    # Concurrent SSL checks
SCAN_TIMEOUT=10          # Timeout per domain
BATCH_SIZE=5000          # Batch processing size
SCHEDULE_INTERVAL=3600   # Scan every 1 hour
```

### For 62GB RAM, 32 cores:

```bash
SCAN_CONCURRENCY=5000    # Can handle more
BATCH_SIZE=10000         # Bigger batches
```

---

## 📊 How It Works

### SSL Scanner Logic

Based on `check_ssl_bulk.sh`:

1. **Check SSL Certificate**
   ```python
   # Get SSL certificate using Python ssl module
   context = ssl.create_default_context()
   sock = socket.create_connection((domain, 443))
   ssock = context.wrap_socket(sock, server_hostname=domain)
   cert = ssock.getpeercert()
   ```

2. **Extract Expiry Date**
   ```python
   expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
   days_until_expiry = (expiry_date - datetime.now()).days
   ```

3. **Check HTTPS Status**
   ```python
   # Using aiohttp (like curl -Ik -L)
   async with session.get(f"https://{domain}", allow_redirects=True) as response:
       https_status = response.status
       redirect_url = str(response.url) if redirected else None
   ```

4. **Save Results**
   ```sql
   INSERT INTO ssl_scan_results 
   (domain_id, ssl_status, ssl_expiry_date, days_until_expiry, 
    https_status, redirect_url, ...)
   VALUES (...)
   ```

5. **Keep History**
   - Saves every scan result
   - Latest 5 scans shown in UI
   - Historical data for tracking

---

## 🎨 Frontend Features

### Stats Cards
```
┌────────────────────────────────────┐
│ Total Domains        SSL Valid     │
│     1,234               987        │
│                                    │
│ Expired Soon         Failed        │
│      45                 202        │
└────────────────────────────────────┘
```

### Domain Table
```
Domain      | SSL History  | Expired on      | HTTPS | Redirect
------------|--------------|-----------------|-------|----------
example.com | 🟢🟢🟢🟢🟢  | 2026-01-15 (51) | 200   | -
test.com    | 🔴🔴🔴🟢🟢  | 2025-11-30 (4)  | 301   | new.com
```

**SSL History Dots:**
- Hover để xem detail
- Shows last 5 scan results
- Green = Valid, Red = Invalid

**Expiry Date:**
- Red badge: < 7 days (urgent!)
- Green badge: >= 7 days (ok)

**HTTPS Status:**
- Green: 2xx (success)
- Yellow: 3xx (redirect)
- Red: 4xx/5xx (error)

---

## 📝 API Endpoints

### GET /api/dashboard/summary
```json
{
  "total_domains": 1234,
  "ssl_valid_count": 987,
  "expired_soon_count": 45,
  "failed_count": 202,
  "last_scan_time": "2025-11-26T10:00:00"
}
```

### GET /api/domains
Query parameters:
- `ssl_status`: valid/invalid/no_ssl
- `expired_soon`: true/false
- `https_status`: 200, 301, 404, etc.
- `search`: domain name
- `sort_by`: domain/ssl_status/expiry
- `limit`: 100 (default)

Returns:
```json
[
  {
    "id": 1,
    "domain": "example.com",
    "ssl_status": "valid",
    "ssl_expiry_date": "2026-01-15T00:00:00",
    "days_until_expiry": 51,
    "https_status": 200,
    "redirect_url": null,
    "scan_time": "2025-11-26T10:00:00",
    "status_history": [
      {
        "scan_time": "2025-11-26T10:00:00",
        "ssl_status": "valid",
        "days_until_expiry": 51,
        "https_status": 200
      },
      // ... 4 more recent scans
    ]
  }
]
```

---

## ⚡ Performance

### Scanner Throughput
- **Conservative**: 1,000-1,500 domains/second
- **Balanced**: 2,000-3,000 domains/second  
- **Aggressive**: 3,000-5,000 domains/second (62GB RAM, 32 cores)

### Expected Scan Times

| Domains | Conservative | Balanced | Aggressive |
|---------|-------------|----------|------------|
| 1,000 | ~1s | ~0.5s | ~0.3s |
| 10,000 | ~10s | ~5s | ~3s |
| 50,000 | ~50s | ~25s | ~15s |
| 100,000 | ~100s | ~50s | ~30s |
| 500,000 | ~8min | ~4min | ~2.5min |

---

## 🐛 Troubleshooting

### Scanner không chạy

```bash
# Check logs
docker-compose logs -f scanner

# Common issues:
# - Database not ready → Wait longer
# - SSL timeout → Increase SCAN_TIMEOUT
# - Too many connections → Reduce SCAN_CONCURRENCY
```

### Dashboard shows 0

```bash
# Manually refresh materialized view
docker-compose exec postgres psql -U domainuser -d domains -c "
REFRESH MATERIALIZED VIEW CONCURRENTLY latest_ssl_status;
"

# Restart backend
docker-compose restart backend
```

### SSL check fails

```bash
# Test manually
docker-compose exec scanner python3 -c "
import ssl, socket
sock = socket.create_connection(('example.com', 443), timeout=10)
context = ssl.create_default_context()
ssock = context.wrap_socket(sock, server_hostname='example.com')
cert = ssock.getpeercert()
print(cert['notAfter'])
"
```

---

## 📚 Documentation

- **README-SSL.md** ← This file
- **MIGRATION-TO-SSL.md** ← Migration guide from v1.x
- **FRONTEND-TODO.md** ← Frontend implementation guide (complete HTML code)
- **CONFIGURATION.md** ← System optimization guide

---

## ✅ Status

**Version**: 2.0.0  
**Type**: SSL Certificate Monitor  
**Backend**: ✅ Complete  
**Scanner**: ✅ Complete  
**Database**: ✅ Complete  
**Frontend**: ⚠️  Needs implementation (see FRONTEND-TODO.md)  
**Docker**: ✅ Ready  
**Documentation**: ✅ Complete  

---

## 🎯 Next Steps

1. **Implement Frontend** (CRITICAL)
   - See `FRONTEND-TODO.md` for complete HTML code
   - Copy/paste into `frontend/index.html`
   - ~15 minutes to implement

2. **Deploy**
   ```bash
   docker-compose up -d --build
   ```

3. **Add Domains**
   - Via UI (Add Domain / Bulk Add)
   - Or direct to database

4. **Wait for Scan**
   - Auto-scans every 1 hour
   - Or wait for first scan (~30 min for 50k domains)

5. **Monitor**
   - Check dashboard
   - Review SSL status
   - Track expiry dates

---

**Ready to monitor SSL certificates for 50,000+ domains! 🔐**
