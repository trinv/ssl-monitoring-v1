# 🚨 CHẠY MIGRATION NGAY!

## ❌ LỖI HIỆN TẠI

```
asyncpg.exceptions.UndefinedTableError: relation "users" does not exist
```

**Nguyên nhân:** Bảng `users` chưa được tạo trong database!

---

## ✅ GIẢI PHÁP - CHẠY 1 TRONG CÁC LỆNH SAU:

### 🎯 OPTION 1: PowerShell (Windows - Recommended)

```powershell
# Mở PowerShell và chạy:
cd "d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1"

# Chạy migration
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql
```

### 🎯 OPTION 2: CMD (Windows)

```cmd
cd "d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1"

type database\simple_auth_migration.sql | docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor
```

### 🎯 OPTION 3: Git Bash / WSL

```bash
cd /d/VNNIC/4.\ CA\ NHAN/Freelancer/Namestar/Monitoring/ssl-monitoring-v1

docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql
```

### 🎯 OPTION 4: Docker Desktop Terminal

```bash
# Trong Docker Desktop, mở terminal của container postgres và chạy:
psql -U ssluser -d ssl_monitor

# Sau đó paste nội dung file database/simple_auth_migration.sql
```

---

## 🔍 SAU KHI CHẠY, KIỂM TRA:

```bash
# Xem các bảng đã tạo
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "\dt"
```

**Phải thấy:**
```
 public | roles    | table | ssluser
 public | sessions | table | ssluser
 public | users    | table | ssluser
```

```bash
# Kiểm tra admin user
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT username, role_id FROM users"
```

**Phải thấy:**
```
 username | role_id
----------+---------
 admin    |       1
```

---

## 🌐 SAU ĐÓ TEST LOGIN:

1. **Mở trình duyệt:** http://YOUR_SERVER
2. **Login:**
   - Username: `admin`
   - Password: `Admin@123`
3. **Phải vào được dashboard!** ✅

---

## ⚠️ NẾU VẪN LỖI

### Lỗi: "password authentication failed"

Database credentials sai. Kiểm tra trong `docker-compose.yml`:
```yaml
POSTGRES_USER: ssluser
POSTGRES_PASSWORD: SSL@Pass123
```

### Lỗi: "database does not exist"

Database chưa được tạo:
```bash
docker exec ssl-monitoring-postgres createdb -U ssluser ssl_monitor
```

### Lỗi: "could not translate host name postgres"

Container postgres chưa chạy:
```bash
docker compose ps
docker compose up -d postgres
```

---

## 📋 NỘI DUNG MIGRATION (Tham khảo)

File `database/simple_auth_migration.sql` sẽ tạo:

1. **roles table** - 2 roles (admin, user)
2. **users table** - User accounts
3. **sessions table** - Login sessions
4. **Admin user** - username: admin, password: Admin@123

---

## 🎯 TÓM TẮT

**CHẠY NGAY LỆNH NÀY (PowerShell):**

```powershell
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql
```

**SAU ĐÓ LOGIN ĐƯỢC!** ✅

---

## 📞 NẾU KHÔNG CHẠY ĐƯỢC

Gửi cho tôi kết quả của lệnh:

```bash
docker compose ps
docker logs ssl-monitoring-postgres | tail -20
```

Để tôi debug thêm!
