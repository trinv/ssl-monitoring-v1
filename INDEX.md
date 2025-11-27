# 🗂️ DOMAIN MONITOR - START HERE

## 📌 BẮT ĐẦU TẠI ĐÂY!

Chào mừng bạn đến với **Domain Monitor** - Hệ thống giám sát 50,000+ tên miền.

**Version 1.1.0** - No Authentication

---

## 🎯 Thông tin nhanh

- **Server IP**: YOUR_IP_ADDRESS
- **Backend Port**: 8080
- **Frontend Port**: 80
- **Authentication**: None - Direct access!
- **Files**: 18 files, ~155KB

---

## ⚠️ QUAN TRỌNG: Đọc trước khi chạy!

### 🔐 Cấu hình BẮT BUỘC

👉 **ĐỌC NGAY:** [`CONFIGURATION.md`](./CONFIGURATION.md)

**Phải làm gì:**
1. Thay đổi database password
2. Cập nhật IP address (nếu cần)
3. Điều chỉnh scanner parameters
4. Thêm Redis password (khuyến nghị)

**Nếu không cấu hình:** Hệ thống có thể chạy nhưng KHÔNG AN TOÀN cho production!

---

## 📖 Bạn muốn làm gì?

### ⚙️ 1. Tôi muốn cấu hình hệ thống (BẮT BUỘC)

👉 **Đọc:** [`CONFIGURATION.md`](./CONFIGURATION.md)

Hướng dẫn chi tiết:
- Thay đổi passwords
- Cập nhật IP/domain
- Điều chỉnh scanner
- Firewall & ports
- Memory settings
- Backup configuration

**Đọc này TRƯỚC KHI chạy docker-compose!**

---

### 🚀 2. Tôi muốn bắt đầu nhanh (5 phút)

👉 **Đọc:** [`QUICKSTART.md`](./QUICKSTART.md)

Hướng dẫn 3 bước:
1. Cấu hình `.env`
2. Run `./start.sh`
3. Access http://YOUR_IP_ADDRESS

**Lưu ý:** Phải cấu hình `.env` trước!

---

### 📚 3. Tôi muốn hiểu hệ thống (20 phút)

👉 **Đọc:** [`README.md`](./README.md)

Bao gồm:
- Kiến trúc hệ thống
- Features overview
- Performance optimization
- Deployment guide
- Database management

---

### 🐛 4. Tôi gặp lỗi

👉 **Đọc:** [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md)

Giải quyết:
- Database connection issues
- Backend API problems
- Scanner not running
- Complete reset guide

**Quick fix:**
```bash
# Database error
./fix-database.sh

# Check logs
docker-compose logs -f
```

---

## 📂 Cấu trúc files

```
domain-monitor/                    [18 files, ~155KB]
│
├── 🎯 INDEX.md                    ← BẠN ĐANG Ở ĐÂY
├── ⚙️ CONFIGURATION.md            ← ⚠️ ĐỌC TRƯỚC KHI CHẠY!
├── ⚡ QUICKSTART.md               ← Bắt đầu nhanh
├── 📖 README.md                   ← Documentation đầy đủ
├── 🔧 TROUBLESHOOTING.md          ← Giải quyết lỗi
├── 📝 CHANGELOG.md                ← Lịch sử thay đổi
│
├── ⚙️  docker-compose.yml         ← Main configuration
├── 🚀 start.sh                    ← Quick start script
├── 🗄️ fix-database.sh             ← Fix database errors
├── 🔧 .env.example                ← Environment template
│
├── 📁 backend/                    ← FastAPI (port 8080)
│   ├── main.py                    ← No authentication
│   ├── requirements.txt
│   └── Dockerfile
│
├── 📁 frontend/                   ← Web UI
│   └── index.html                 ← Dashboard (no login)
│
├── 📁 scanner/                    ← 50k+ optimized
│   ├── scanner.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── 📁 database/                   ← PostgreSQL
│   └── init.sql                   ← No users table
│
└── 📁 nginx/                      ← Web server
    └── nginx.conf
```

---

## 🎯 Use Cases

### 🆕 Tôi lần đầu deploy
1. **BẮT BUỘC:** Đọc [`CONFIGURATION.md`](./CONFIGURATION.md)
2. Edit `.env` file
3. Run `./start.sh`
4. Access http://YOUR_IP_ADDRESS

### 🔧 Tôi muốn customize
1. Đọc [`CONFIGURATION.md`](./CONFIGURATION.md) → Các thông số
2. Edit `.env` & `docker-compose.yml`
3. Restart: `docker-compose restart`

### 🐛 Tôi gặp lỗi
1. **Database error?** Run `./fix-database.sh`
2. **Not sure?** Check [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md)
3. **Still stuck?** `docker-compose logs -f`

---

## ⚡ Quick Commands

```bash
# Cấu hình (BẮT BUỘC trước khi start!)
cp .env.example .env
nano .env    # ⚠️ THAY ĐỔI PASSWORD!

# Start
./start.sh
# hoặc
docker-compose up -d --build

# View logs
docker-compose logs -f

# Restart service
docker-compose restart backend

# Stop all
docker-compose stop
```

---

## ✨ Key Features

### ✅ No Authentication
- Direct access to dashboard
- No login/logout needed
- Simplified deployment
- Faster access

### ✅ Production Ready
- Docker containerized
- Configuration guide
- Complete documentation
- 50k+ domains support

### ✅ Optimized Performance
- 2,000 concurrent scans
- Batch processing (5,000/batch)
- PostgreSQL COPY bulk insert
- Memory efficient

### ✅ Clean & Simple
- 18 files only
- No authentication complexity
- Clear structure
- Easy to configure

---

## 🔑 Key Configuration

### ⚠️ BẮT BUỘC cấu hình:

1. **Database Password** (`.env`)
   ```bash
   POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD
   DATABASE_URL=postgresql://domainuser:YOUR_SECURE_PASSWORD@postgres:5432/domains
   ```

2. **IP Address** (nếu khác YOUR_IP_ADDRESS)
   - `frontend/index.html` → API_BASE_URL
   - `nginx/nginx.conf` → server_name

3. **Scanner** (`.env` - tùy chỉnh theo server)
   ```bash
   SCAN_CONCURRENCY=2000
   BATCH_SIZE=5000
   SCHEDULE_INTERVAL=3600
   ```

Xem chi tiết: [`CONFIGURATION.md`](./CONFIGURATION.md)

---

## 📥 Download Options

### Option 1: Folder
📁 Browse folder: [`domain-monitor/`](.)

### Option 2: Archive
📦 Download: [`domain-monitor.tar.gz`](../domain-monitor.tar.gz)

```bash
# Extract
tar -xzf domain-monitor.tar.gz

# Configure (IMPORTANT!)
cd domain-monitor
cp .env.example .env
nano .env

# Start
./start.sh
```

---

## 🎓 Learning Path

### Beginner (20 phút)
1. [`CONFIGURATION.md`](./CONFIGURATION.md) - **BẮT BUỘC đọc**
2. [`QUICKSTART.md`](./QUICKSTART.md) - Deploy
3. Access dashboard và test

### Intermediate (1 giờ)
1. [`README.md`](./README.md) - Hiểu hệ thống
2. Test các features
3. Customize scanner parameters

### Advanced (4+ giờ)
1. Đọc source code
2. Optimize for scale
3. Setup monitoring
4. Deploy to production

---

## ✅ Deployment Checklist

### Before Deploy (BẮT BUỘC)
- [ ] Đọc [`CONFIGURATION.md`](./CONFIGURATION.md)
- [ ] Copy `.env.example` → `.env`
- [ ] Thay đổi `POSTGRES_PASSWORD` trong `.env`
- [ ] Update `DATABASE_URL` với password mới
- [ ] Update IP trong `frontend/index.html` (nếu cần)
- [ ] Update `server_name` trong `nginx/nginx.conf` (nếu cần)
- [ ] Điều chỉnh scanner parameters
- [ ] Check firewall (ports 80, 8080)

### After Deploy
- [ ] Run `./start.sh`
- [ ] Check services: `docker-compose ps`
- [ ] Access http://YOUR_IP
- [ ] Add test domains
- [ ] Trigger scan
- [ ] Monitor logs

---

## 🆘 Need Help?

### Quick Fixes

**Cannot access website?**
```bash
docker-compose logs nginx
docker-compose restart nginx
```

**Backend not working?**
```bash
docker-compose logs backend
curl http://YOUR_IP:8080/
docker-compose restart backend
```

**Database error?**
```bash
./fix-database.sh
```

### Full Troubleshooting
👉 See [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md)

---

## 🎉 Ready!

Bạn đã sẵn sàng để:

✅ Configure hệ thống  
✅ Deploy production  
✅ Monitor 50,000+ domains  
✅ Access without login  
✅ Scale khi cần  

**Next Step:** 
1. Đọc [`CONFIGURATION.md`](./CONFIGURATION.md) ← **BẮT BUỘC**
2. Configure `.env`
3. Run `./start.sh`
4. Access http://YOUR_IP_ADDRESS

---

## 📊 Package Info

| Metric | Value |
|--------|-------|
| **Total Files** | 18 |
| **Size** | ~155 KB |
| **Compressed** | ~38 KB |
| **Version** | 1.1.0 |
| **Authentication** | None |
| **Status** | ✅ Production Ready |

---

**Happy Monitoring! 🚀**

**⚠️ REMEMBER: Read CONFIGURATION.md before deploying!**
