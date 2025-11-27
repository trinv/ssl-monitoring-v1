# ⚙️ CONFIGURATION GUIDE

## 📋 Hướng dẫn cấu hình trước khi chạy

**QUAN TRỌNG**: Đọc và thực hiện các bước này TRƯỚC KHI chạy `docker-compose up`

---

## 🔐 1. THAY ĐỔI MẬT KHẨU DATABASE

### ⚠️ **BẮT BUỘC cho production!**

#### File cần sửa: `.env`

```bash
# Copy file mẫu
cp .env.example .env

# Sửa file .env
nano .env
```

#### Các thông số cần thay đổi:

```bash
# ==================== DATABASE ====================
# ⚠️ THAY ĐỔI MẬT KHẨU NÀY!
POSTGRES_USER=domainuser           # Có thể đổi
POSTGRES_PASSWORD=domainpass123    # ⚠️ PHẢI ĐỔI!
POSTGRES_DB=domains

# Connection string (cập nhật password ở đây)
DATABASE_URL=postgresql://domainuser:domainpass123@postgres:5432/domains
#                                    ↑↑↑↑↑↑↑↑↑↑↑↑↑
#                              THAY ĐỔI MẬT KHẨU NÀY
```

**Ví dụ mật khẩu mạnh:**
```bash
POSTGRES_PASSWORD=Dm#2024@Secure!Pass789
DATABASE_URL=postgresql://domainuser:Dm#2024@Secure!Pass789@postgres:5432/domains
```

**Tạo mật khẩu ngẫu nhiên:**
```bash
# Linux/Mac
openssl rand -base64 32

# Hoặc
pwgen -s 32 1
```

---

### File cần sửa: `.env` và `docker-compose.yml`

#### Bước 1: Thêm password vào `.env`

```bash
#### Bước 2: Sửa `docker-compose.yml`

```yaml
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --requirepass YourRedisPassword123    # ⚠️ THÊM DÒnG NÀY
    --appendonly yes
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru
```

---

## 🌐 3. THAY ĐỔI IP ADDRESS

### Nếu IP server khác YOUR_IP_ADDRESS

#### File cần sửa: `frontend/index.html`

```javascript
// Tìm dòng này (khoảng dòng 350)
const API_BASE_URL = 'http://YOUR_IP_ADDRESS:8080/api';

// Thay đổi thành IP của bạn
const API_BASE_URL = 'http://YOUR_SERVER_IP:8080/api';
```

#### File cần sửa: `nginx/nginx.conf`

```nginx
server {
    listen 80;
    server_name YOUR_IP_ADDRESS;    # ⚠️ Thay đổi IP ở đây
    
    # Hoặc dùng domain
    # server_name yourdomain.com;
}
```

---

## 🔧 4. TÙY CHỈNH SCANNER

### File cần sửa: `.env`

```bash
# ==================== SCANNER ====================

# Số lượng domains scan đồng thời
# Tăng lên nếu server mạnh, giảm xuống nếu server yếu
SCAN_CONCURRENCY=2000              # Mặc định: 2000
# Khuyến nghị:
# - Server yếu (2GB RAM): 500-1000
# - Server trung bình (4GB RAM): 1000-2000
# - Server mạnh (8GB+ RAM): 2000-3000

# Số domains xử lý mỗi batch
BATCH_SIZE=5000                    # Mặc định: 5000
# Khuyến nghị:
# - Ít domains (<10k): 1000-2000
# - Nhiều domains (10k-50k): 5000
# - Rất nhiều (>50k): 10000

# Timeout cho mỗi domain (giây)
SCAN_TIMEOUT=10                    # Mặc định: 10
# Tăng lên nếu domains phản hồi chậm

# Khoảng thời gian giữa các lần scan (giây)
SCHEDULE_INTERVAL=3600             # Mặc định: 3600 (1 giờ)
# 1800 = 30 phút
# 7200 = 2 giờ
# 86400 = 24 giờ
```

**Tính toán thời gian scan:**
```
Thời gian ước tính = (Số domains / SCAN_CONCURRENCY) * SCAN_TIMEOUT

Ví dụ với 50,000 domains:
= (50000 / 2000) * 10
= 25 * 10
= 250 giây = ~4 phút (thời gian tối thiểu)

Thực tế thường mất 50-60 phút do network latency, retries, etc.
```

---

## 💾 5. ĐIỀU CHỈNH MEMORY

### File cần sửa: `docker-compose.yml`

#### Redis Memory:

```yaml
redis:
  command: >
    redis-server
    --maxmemory 2gb              # ⚠️ Điều chỉnh theo RAM server
    --maxmemory-policy allkeys-lru
```

**Khuyến nghị:**
- Server 4GB RAM: `maxmemory 1gb`
- Server 8GB RAM: `maxmemory 2gb`
- Server 16GB+ RAM: `maxmemory 4gb`

#### PostgreSQL:

Thêm resource limits (optional):

```yaml
postgres:
  # ... existing config ...
  deploy:
    resources:
      limits:
        memory: 2G               # ⚠️ Điều chỉnh
      reservations:
        memory: 1G
```

---

## 🔧 6. DATABASE CONNECTION POOL

### File cần sửa: `backend/main.py`

```python
# Tìm dòng này (khoảng dòng 25-30)
db_pool = await asyncpg.create_pool(
    DATABASE_URL, 
    min_size=10,         # ⚠️ Có thể điều chỉnh
    max_size=50,         # ⚠️ Có thể điều chỉnh
    command_timeout=60
)
```

**Khuyến nghị:**
- Ít domains (<10k): `max_size=20`
- Trung bình (10k-50k): `max_size=50`
- Nhiều (>50k): `max_size=100`

**Lưu ý**: PostgreSQL mặc định cho phép max 100 connections

---

## 🔒 7. FIREWALL & PORTS

### Ports cần mở:

```bash
# HTTP (Frontend)
sudo ufw allow 80/tcp

# API Backend
sudo ufw allow 8080/tcp

# Optional: HTTPS
# sudo ufw allow 443/tcp
```

### Kiểm tra ports:

```bash
# Xem ports đang mở
sudo netstat -tlnp | grep -E '(80|8080)'

# Test từ máy khác
curl http://YOUR_SERVER_IP
curl http://YOUR_SERVER_IP:8080
```

---

## 📁 8. VOLUME & BACKUP

### Backup Configuration:

Thêm vào `docker-compose.yml` nếu muốn backup tự động:

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: /path/to/backup/postgres   # ⚠️ Chỉ định đường dẫn
      o: bind
```

### Manual Backup Script:

Tạo file `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/domain-monitor"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U domainuser domains | \
  gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup volumes
docker run --rm \
  -v domain-monitor_postgres_data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/volumes_$DATE.tar.gz /data

echo "Backup completed: $BACKUP_DIR"
```

---

## 🌐 9. DOMAIN NAME & SSL (Optional)

### Nếu dùng domain thay vì IP:

#### File: `nginx/nginx.conf`

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;   # ⚠️ Thay domain
    
    # Redirect to HTTPS (nếu có SSL)
    # return 301 https://$server_name$request_uri;
}

# HTTPS (nếu có SSL certificate)
# server {
#     listen 443 ssl http2;
#     server_name yourdomain.com;
#     
#     ssl_certificate /etc/nginx/ssl/cert.pem;        # ⚠️ Đường dẫn cert
#     ssl_certificate_key /etc/nginx/ssl/key.pem;     # ⚠️ Đường dẫn key
#     
#     # ... rest of config ...
# }
```

#### Frontend: `frontend/index.html`

```javascript
const API_BASE_URL = 'https://yourdomain.com:8080/api';  // HTTPS
// hoặc
const API_BASE_URL = 'https://api.yourdomain.com/api';   // Subdomain
```

---

## 📊 10. LOGGING & MONITORING

### Log Rotation (Recommended):

Tạo file `/etc/logrotate.d/docker-containers`:

```bash
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
    maxsize 100M
}
```

### Scanner Logs:

File: `docker-compose.yml`

```yaml
scanner:
  # ... existing config ...
  logging:
    driver: "json-file"
    options:
      max-size: "10m"      # ⚠️ Điều chỉnh
      max-file: "3"
```

---

## ✅ CHECKLIST CẤU HÌNH

Trước khi chạy `docker-compose up`, kiểm tra:

### Bắt buộc:
- [ ] Đã copy `.env.example` sang `.env`
- [ ] Đã thay đổi `POSTGRES_PASSWORD`
- [ ] Đã cập nhật `DATABASE_URL` với password mới
- [ ] Đã thay đổi IP trong `frontend/index.html` (nếu cần)
- [ ] Đã thay đổi `server_name` trong `nginx/nginx.conf` (nếu cần)

### Khuyến nghị:
### Optional:
- [ ] Đã cấu hình domain name
- [ ] Đã setup SSL certificate
- [ ] Đã cấu hình log rotation
- [ ] Đã test từ máy khác

---

## 🚀 SAU KHI CẤU HÌNH

### 1. Build và start:

```bash
docker-compose up -d --build
```

### 2. Kiểm tra logs:

```bash
# Xem tất cả
docker-compose logs -f

# Xem từng service
docker-compose logs -f postgres
docker-compose logs -f backend
docker-compose logs -f scanner
```

### 3. Test kết nối:

```bash
# Test backend API
curl http://YOUR_IP:8080/

# Test frontend
curl http://YOUR_IP/

# Test database
docker-compose exec postgres psql -U domainuser -d domains -c "SELECT 1;"
```

### 4. Monitor:

```bash
# Xem resource usage
docker stats

# Xem scanner progress
docker-compose logs -f scanner | grep "Scan completed"
```

---

## 📖 TÀI LIỆU THAM KHẢO

**File .env đầy đủ:**
```bash
# ==================== DATABASE ====================
POSTGRES_USER=domainuser
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_HERE    # ⚠️ THAY ĐỔI
POSTGRES_DB=domains
DATABASE_URL=postgresql://domainuser:YOUR_SECURE_PASSWORD_HERE@postgres:5432/domains

# ==================== SCANNER ====================
SCAN_CONCURRENCY=2000      # Domains scan đồng thời
BATCH_SIZE=5000            # Domains mỗi batch
SCAN_TIMEOUT=10            # Timeout (giây)
SCHEDULE_INTERVAL=3600     # Khoảng cách scan (giây)

# ==================== SERVER ====================
SERVER_IP=YOUR_IP_ADDRESS    # ⚠️ Thay đổi nếu cần
BACKEND_PORT=8080
FRONTEND_PORT=80
```

**Các file quan trọng:**
- `.env` - Environment variables
- `docker-compose.yml` - Services configuration
- `frontend/index.html` - API endpoint (line ~350)
- `nginx/nginx.conf` - Server name và SSL
- `backend/main.py` - Database pool size

---

## 🆘 TRỢ GIÚP

Nếu sau khi cấu hình gặp vấn đề:

1. **Check logs**: `docker-compose logs -f`
2. **Restart services**: `docker-compose restart`
3. **Reset database**: `./fix-database.sh`
4. **Full restart**: 
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

Xem thêm: `TROUBLESHOOTING.md`

---

**Version**: 1.1.0 (No Authentication)  
**Last Updated**: November 2025  
**Configuration Required**: ✅ Bắt buộc trước khi deploy
