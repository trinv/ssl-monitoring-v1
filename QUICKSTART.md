# ⚡ QUICKSTART - Domain Monitor

## 🎯 Version 1.1.0 - No Authentication

- **Server**: 74.48.129.112:8080  
- **Access**: Direct (no login needed)  
- **Max Domains**: 50,000+

---

## ⚠️ TRƯỚC KHI BẮT ĐẦU

### BẮT BUỘC: Đọc Configuration Guide

👉 **[CONFIGURATION.md](./CONFIGURATION.md)** - Hướng dẫn chi tiết

**Phải làm:**
- Thay đổi database password
- Cập nhật IP address (nếu cần)
- Điều chỉnh scanner parameters

**Nếu bỏ qua:** Hệ thống không an toàn cho production!

---

## 🚀 3 bước khởi động

### 1️⃣ Cấu hình Environment

```bash
# Copy file template
cp .env.example .env

# SỬA FILE .ENV - QUAN TRỌNG!
nano .env
```

**Thay đổi BẮT BUỘC trong `.env`:**

```bash
# ⚠️ THAY ĐỔI PASSWORD NÀY!
POSTGRES_PASSWORD=domainpass123    # ← Đổi password mạnh
DATABASE_URL=postgresql://domainuser:domainpass123@postgres:5432/domains
#                                    ↑↑↑↑↑↑↑↑↑↑↑↑↑
#                              Cập nhật password ở đây

# Tùy chỉnh theo server của bạn
SCAN_CONCURRENCY=2000    # Server mạnh: 2000-3000, yếu: 500-1000
BATCH_SIZE=5000          # Số domains mỗi batch
SCHEDULE_INTERVAL=3600   # 1 giờ = 3600 giây
```

**Tạo password mạnh:**
```bash
openssl rand -base64 32
```

---

### 2️⃣ Chạy hệ thống

```bash
# Cách 1: Script tự động (khuyến nghị)
chmod +x start.sh
./start.sh

# Cách 2: Thủ công
docker-compose up -d --build
```

**Đợi services khởi động (30 giây):**
```bash
# Xem tiến trình
docker-compose logs -f
```

---

### 3️⃣ Truy cập

```
URL: http://74.48.129.112
```

**Không cần login** - Truy cập trực tiếp dashboard!

---

## 📁 Cấu trúc files (18 files, 155KB)

```
domain-monitor/
├── CONFIGURATION.md         ⚠️ Đọc trước khi chạy!
├── QUICKSTART.md           ← File này
├── README.md               ← Full documentation
├── TROUBLESHOOTING.md      ← Giải quyết lỗi
├── CHANGELOG.md            ← Version history
│
├── .env.example            ← Template (PHẢI COPY & SỬA!)
├── docker-compose.yml
├── start.sh
├── fix-database.sh
│
├── backend/                [3 files]
├── frontend/               [1 file - index.html]
├── scanner/                [3 files]
├── database/               [1 file - init.sql]
└── nginx/                  [1 file - nginx.conf]
```

---

## ⚙️ Cấu hình quan trọng

### 🔐 1. Database Password (BẮT BUỘC)

**File:** `.env`

```bash
# THAY ĐỔI PASSWORD!
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_HERE
DATABASE_URL=postgresql://domainuser:YOUR_SECURE_PASSWORD_HERE@postgres:5432/domains
```

---

### 🌐 2. IP Address (Nếu khác 74.48.129.112)

**File 1:** `frontend/index.html` (dòng ~350)

```javascript
const API_BASE_URL = 'http://YOUR_SERVER_IP:8080/api';
```

**File 2:** `nginx/nginx.conf`

```nginx
server_name YOUR_SERVER_IP;
```

---

### 🔧 3. Scanner Parameters

**File:** `.env`

```bash
# Điều chỉnh theo server
SCAN_CONCURRENCY=2000    # Server yếu: 500-1000, mạnh: 2000-3000
BATCH_SIZE=5000          # Batch processing size
SCAN_TIMEOUT=10          # Timeout per domain (seconds)
SCHEDULE_INTERVAL=3600   # Scan every 1 hour (3600s)
```

**Tính toán:**
- **50,000 domains** với `SCAN_CONCURRENCY=2000` → ~50-60 phút
- **10,000 domains** với `SCAN_CONCURRENCY=1000` → ~10-15 phút

---

## ✅ Kiểm tra sau khi chạy

### 1. Services đang chạy

```bash
docker-compose ps
```

**Expected:**
```
domain-monitor-postgres   Up
domain-monitor-redis      Up
domain-monitor-backend    Up
domain-monitor-scanner    Up
domain-monitor-nginx      Up
```

---

### 2. Backend API hoạt động

```bash
curl http://74.48.129.112:8080/
```

**Expected:**
```json
{
  "status": "ok",
  "message": "Domain Monitoring API - No Auth",
  "version": "1.1.0",
  "port": 8080
}
```

---

### 3. Frontend accessible

```bash
curl http://74.48.129.112/
```

**Expected:** HTML content of dashboard

---

### 4. Database initialized

```bash
docker-compose exec postgres psql -U domainuser -d domains -c "SELECT COUNT(*) FROM domains;"
```

**Expected:** Number (0 initially)

---

## 🎨 Sử dụng Dashboard

### Truy cập
```
http://74.48.129.112
```

### Features
1. **Dashboard** - 4 stats cards + chart
2. **Add Domain** - Add single domain
3. **Bulk Add** - Paste domain list
4. **Search** - Find domains
5. **Filter** - By status (All, Is For Sale, Failed, Other)
6. **Export CSV** - Download data
7. **Trigger Scan** - Manual scan

### Add domains

**Method 1: Single**
- Click "Add Domain"
- Enter domain name
- Optional notes
- Click "Add"

**Method 2: Bulk**
- Click "Bulk Add"
- Paste list (one per line):
  ```
  example1.com
  example2.com
  example3.com
  ```
- Click "Add All"

---

## ❗ Troubleshooting

### ❌ Cannot access http://74.48.129.112

```bash
# Check services
docker-compose ps

# Check nginx
docker-compose logs nginx

# Restart nginx
docker-compose restart nginx
```

---

### ❌ Database errors

```bash
# Check logs
docker-compose logs postgres

# Fix database
./fix-database.sh
```

---

### ❌ Backend not responding (port 8080)

```bash
# Check logs
docker-compose logs backend

# Test API
curl http://74.48.129.112:8080/

# Restart
docker-compose restart backend
```

---

### ❌ Scanner not running

```bash
# View logs
docker-compose logs -f scanner

# Restart
docker-compose restart scanner
```

---

## 🔄 Lệnh thường dùng

```bash
# Start all services
docker-compose up -d

# View logs (all)
docker-compose logs -f

# View logs (specific)
docker-compose logs -f backend
docker-compose logs -f scanner

# Restart service
docker-compose restart backend

# Stop all
docker-compose stop

# Remove everything (including data!)
docker-compose down -v

# Backup database
docker-compose exec postgres pg_dump -U domainuser domains > backup.sql
```

---

## 📊 Monitor Scanner

### View real-time logs

```bash
docker-compose logs -f scanner
```

**You'll see:**
```
Processing batch: 0-5000 of 50000
Batch completed in 45.2s - For Sale: 123, Failed: 45, Other: 4832
Processing batch: 5000-10000 of 50000
...
Scan Completed Successfully!
Total scanned: 50000 domains
Is For Sale: 2456
Failed: 891
Other: 46653
Total duration: 3245s (54.1 minutes)
Throughput: 15.4 domains/second
```

---

## 🎯 Next Steps

### 1. Add your domains
- Bulk add from file
- Or add individually

### 2. Wait for scan
- Auto-scans every 1 hour (default)
- Or trigger manually

### 3. View results
- Dashboard shows stats
- Filter by status
- Export to CSV

### 4. Optimize
- Adjust `SCAN_CONCURRENCY`
- Adjust `BATCH_SIZE`
- Change `SCHEDULE_INTERVAL`

---

## 📖 More Information

- **Full docs:** [README.md](./README.md)
- **Configuration:** [CONFIGURATION.md](./CONFIGURATION.md) ← **BẮT BUỘC đọc**
- **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Changes:** [CHANGELOG.md](./CHANGELOG.md)

---

## ✅ Success Checklist

- [ ] Đọc [CONFIGURATION.md](./CONFIGURATION.md)
- [ ] Copy `.env.example` → `.env`
- [ ] Thay đổi `POSTGRES_PASSWORD`
- [ ] Update IP (nếu cần)
- [ ] Run `./start.sh`
- [ ] Check services: `docker-compose ps`
- [ ] Access http://YOUR_IP
- [ ] Add test domains
- [ ] Wait for scan
- [ ] View results

---

**Version**: 1.1.0 (No Authentication)  
**Setup Time**: ~5-10 minutes  
**Status**: ✅ Production Ready

**⚠️ REMEMBER:** Read CONFIGURATION.md before deploying!
