# 📤 Push to GitHub Guide

## 🎯 Chuẩn bị Push lên GitHub

### Bước 1: Tạo Repository trên GitHub

1. Đăng nhập vào GitHub
2. Click **"New repository"**
3. Điền thông tin:
   - **Repository name:** `ssl-monitoring` (hoặc tên khác)
   - **Description:** `SSL Certificate Monitoring System with Authentication`
   - **Visibility:** Private (khuyến nghị) hoặc Public
   - **KHÔNG** chọn "Initialize with README" (vì đã có README)
4. Click **"Create repository"**

---

### Bước 2: Chuẩn bị Local Repository

```bash
# Di chuyển vào thư mục project
cd "d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1"

# Khởi tạo Git repository (nếu chưa có)
git init

# Thêm tất cả files
git add .

# Commit lần đầu
git commit -m "Initial commit - SSL Monitoring System with Authentication"
```

---

### Bước 3: Kết nối với GitHub

Thay `YOUR_USERNAME` và `REPO_NAME` bằng thông tin thực tế:

```bash
# Thêm remote repository
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Hoặc nếu dùng SSH
git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git

# Kiểm tra remote
git remote -v
```

---

### Bước 4: Push lên GitHub

```bash
# Push lên GitHub (branch main)
git branch -M main
git push -u origin main
```

Nếu gặp lỗi xác thực:
- **HTTPS:** Nhập GitHub username và Personal Access Token (không phải password)
- **SSH:** Đảm bảo đã cấu hình SSH key

---

## 📋 Files Quan Trọng Đã Được Chuẩn Bị

### Files cho Deployment:
- ✅ **`deploy.sh`** - Script deploy tự động cho môi trường mới
- ✅ **`DEPLOYMENT_GUIDE.md`** - Hướng dẫn deploy chi tiết
- ✅ **`.gitignore`** - Loại trừ files không cần thiết
- ✅ **`README_GITHUB.md`** - README cho GitHub

### Files Backend:
- ✅ `backend/main.py` - FastAPI application
- ✅ `backend/auth/` - Auth module (models, routes, utils, dependencies)
- ✅ `backend/Dockerfile` - Docker image cho backend
- ✅ `backend/requirements.txt` - Python dependencies

### Files Frontend:
- ✅ `frontend/index.html` - Dashboard với auth check
- ✅ `frontend/login.html` - Login page
- ✅ `frontend/js/auth.js` - Auth logic
- ✅ `frontend/js/` - Các module JS khác
- ✅ `frontend/css/style.css` - Custom styles

### Files Database:
- ✅ `database/init.sql` - Schema cho domains
- ✅ `database/auth_migration.sql` - Schema cho authentication

### Files Docker:
- ✅ `docker-compose.yml` - Docker services configuration

---

## 🔒 Đổi Tên README (Khuyến nghị)

Trước khi push, đổi tên README để phù hợp:

```bash
# Xóa README cũ (nếu có)
rm README.md

# Đổi tên README mới
mv README_GITHUB.md README.md

# Commit lại
git add README.md
git commit -m "Update README for GitHub"
```

---

## 🚀 Sau Khi Push lên GitHub

### Clone về Môi Trường Mới:

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
cd REPO_NAME

# Deploy tự động
chmod +x deploy.sh
./deploy.sh
```

Script `deploy.sh` sẽ tự động:
1. ✅ Build Docker images
2. ✅ Start services
3. ✅ Đợi PostgreSQL sẵn sàng
4. ✅ Chạy migrations
5. ✅ Tạo admin user
6. ✅ Verify deployment

---

## 📝 Cấu Trúc Repository Trên GitHub

```
ssl-monitoring/
├── README.md                    # Main documentation
├── DEPLOYMENT_GUIDE.md          # Deployment instructions
├── AUTH_SETUP.md                # Auth configuration
├── CHANGELOG_AUTH.md            # Changes log
├── .gitignore                   # Git ignore rules
├── deploy.sh                    # Deployment script
├── docker-compose.yml           # Docker services
├── backend/
│   ├── main.py
│   ├── auth/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── entrypoint.sh
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── css/
│   └── js/
├── database/
│   ├── init.sql
│   └── auth_migration.sql
└── scanner/
    └── scanner.sh
```

---

## ✅ Checklist Trước Khi Push

- [ ] Đã test toàn bộ hệ thống locally
- [ ] Đã xóa/gitignore các file nhạy cảm (.env, passwords, etc.)
- [ ] Đã kiểm tra `.gitignore` hoạt động đúng
- [ ] Đã đổi tên README_GITHUB.md → README.md
- [ ] Đã test script `deploy.sh` hoạt động
- [ ] Đã review tất cả files sẽ được push
- [ ] Đã chuẩn bị repository trên GitHub

---

## 🔐 Bảo Mật

### QUAN TRỌNG - KHÔNG commit:

- ❌ Passwords thực tế
- ❌ API keys
- ❌ Database dumps có data nhạy cảm
- ❌ `.env` files với secrets
- ❌ Private keys

### Đã được gitignore:

- ✅ `.env` files
- ✅ Database data (`postgres_data/`)
- ✅ Log files
- ✅ Temporary files
- ✅ Python cache
- ✅ IDE configs

---

## 📊 Kiểm Tra Files Sẽ Push

```bash
# Xem các files sẽ được commit
git status

# Xem diff
git diff

# Xem files sẽ được push
git ls-files
```

---

## 🔄 Update Sau Này

Khi có thay đổi:

```bash
# Thêm changes
git add .

# Commit với message rõ ràng
git commit -m "Add feature X"
# hoặc
git commit -m "Fix bug Y"
# hoặc
git commit -m "Update configuration Z"

# Push lên GitHub
git push origin main
```

---

## 🌟 Best Practices

### Commit Messages:

- ✅ **Good:** "Add user management UI"
- ✅ **Good:** "Fix login redirect issue"
- ✅ **Good:** "Update deployment documentation"
- ❌ **Bad:** "update"
- ❌ **Bad:** "fix"
- ❌ **Bad:** "changes"

### Branches:

Nếu làm việc nhóm:
```bash
# Tạo branch mới cho feature
git checkout -b feature/user-management

# Push branch
git push -u origin feature/user-management

# Merge về main sau khi review
```

---

## 📞 Hỗ Trợ

### Các lệnh Git hữu ích:

```bash
# Xem status
git status

# Xem history
git log --oneline

# Xem remote
git remote -v

# Xem branches
git branch -a

# Hủy changes chưa commit
git checkout -- <file>

# Reset về commit trước
git reset --hard HEAD~1

# Pull latest từ GitHub
git pull origin main
```

---

## 🎉 Hoàn Tất!

Sau khi push thành công:

1. ✅ Code đã được backup trên GitHub
2. ✅ Có thể clone về bất kỳ môi trường nào
3. ✅ Script `deploy.sh` sẵn sàng cho deployment
4. ✅ Documentation đầy đủ cho người khác

**Repository của bạn:** `https://github.com/YOUR_USERNAME/REPO_NAME`

Happy coding! 🚀
