# ⚡ Quick Start - SSL Monitor

## 🎯 Cho Người Dùng Mới (Clone từ GitHub)

### 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/ssl-monitoring.git
cd ssl-monitoring
```

### 2️⃣ Deploy (Một lệnh duy nhất)

```bash
chmod +x deploy.sh
./deploy.sh
```

### 3️⃣ Truy Cập

- **URL:** http://YOUR_SERVER_IP:8888
- **Login:** admin / Admin@123

**Xong!** ✅

---

## 📤 Cho Người Phát Triển (Push lên GitHub)

### Lần Đầu Tiên:

```bash
# Trong thư mục project
cd "d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1"

# Đổi tên README
rm README.md
mv README_GITHUB.md README.md

# Commit và push
git init
git add .
git commit -m "Initial commit - SSL Monitoring System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git push -u origin main
```

### Update Sau Này:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

---

## 🛠️ Quản Lý Hệ Thống

### Xem Logs:
```bash
docker compose logs -f
```

### Restart Services:
```bash
docker compose restart
```

### Stop All:
```bash
docker compose down
```

### Backup Database:
```bash
docker exec ssl-monitoring-postgres pg_dump -U ssluser ssl_monitor > backup.sql
```

---

## 📚 Chi Tiết Hơn?

- **Deploy mới:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Push lên GitHub:** [PUSH_TO_GITHUB.md](PUSH_TO_GITHUB.md)
- **Cấu hình Auth:** [AUTH_SETUP.md](AUTH_SETUP.md)
- **API Docs:** http://localhost:8080/docs (khi chạy)

---

## 🆘 Troubleshooting

### Backend lỗi?
```bash
docker compose logs backend
docker compose restart backend
```

### Database lỗi?
```bash
docker compose restart postgres
sleep 30
docker compose restart backend
```

### Không login được?
```bash
# Run migration lại
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql
```

---

## ✅ Tất cả trong một file!

**3 bước deploy:** Clone → `./deploy.sh` → Truy cập web

**Đơn giản vậy thôi!** 🚀
