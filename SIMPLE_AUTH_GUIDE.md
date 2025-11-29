# 🔐 Simple Authentication Guide

## 📋 Overview

Hệ thống authentication đã được đơn giản hóa theo yêu cầu:

### ✅ Tính năng đơn giản:
- Login bằng username + password
- Kiểm tra thông tin qua database
- Lưu session token khi login thành công
- 2 quyền: **admin** (full access) và **user** (limited access)

### ❌ Đã loại bỏ:
- Session expiry phức tạp
- Account locking
- Audit logs
- Permissions chi tiết
- Email validation

---

## 🗄️ Database Schema (Simplified)

### 3 bảng chính:

1. **roles** - 2 vai trò: admin, user
2. **users** - Tài khoản người dùng
3. **sessions** - Token đăng nhập

```sql
-- roles: chỉ 2 roles
id | role_name | description
1  | admin     | Administrator - Full access
2  | user      | User - Limited access

-- users: thông tin đơn giản
id | username | password_hash | full_name | role_id | is_active

-- sessions: lưu token
id | user_id | session_token | created_at
```

---

## 🔐 Default Account

**Admin account:**
- Username: `admin`
- Password: `Admin@123`
- Role: admin (full access)

---

## 🚀 Deployment

### Option 1: Sử dụng Simple Auth (Recommended)

```bash
# Run simple migration
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql
```

### Option 2: Replace Files

Thay thế các file cũ bằng file mới:

```bash
cd backend/auth/

# Backup old files
mv models.py models.py.backup
mv routes.py routes.py.backup
mv dependencies.py dependencies.py.backup

# Use simple versions
cp simple_models.py models.py
cp simple_routes.py routes.py
cp simple_dependencies.py dependencies.py
```

Frontend:

```bash
cd frontend/js/

# Backup
mv auth.js auth.js.backup

# Use simple version
cp simple_auth.js auth.js
```

---

## 🔑 Authentication Flow

### 1. Login Process

```
User enters username + password
    ↓
Frontend sends POST /api/auth/login
    ↓
Backend checks users table
    ↓
Verify password (bcrypt)
    ↓
If valid: Generate session token
    ↓
Save token to sessions table
    ↓
Return token + user info to frontend
    ↓
Frontend saves token to localStorage
    ↓
Redirect to dashboard
```

### 2. Access Protected Page

```
User accesses dashboard
    ↓
Frontend checks localStorage for token
    ↓
If no token: Redirect to login
    ↓
If has token: Send with request headers
    ↓
Backend checks sessions table
    ↓
If valid: Return data
    ↓
If invalid: Return 401
    ↓
Frontend redirects to login
```

### 3. Logout

```
User clicks logout
    ↓
Frontend sends POST /api/auth/logout
    ↓
Backend deletes session from table
    ↓
Frontend clears localStorage
    ↓
Redirect to login page
```

---

## 👥 User Roles & Access

### Admin (role_id=1)
✅ **Can do everything:**
- View all domains
- Add/edit/delete domains
- Trigger scans
- Export data
- **Create/edit/delete users**
- **Change user roles**
- **Enable/disable users**

### User (role_id=2)
✅ **Can do:**
- View domains
- Add domains (optional - can restrict)
- Change own password

❌ **Cannot do:**
- Manage other users
- Change own role
- Access admin features

---

## 📡 API Endpoints

### Public (No Auth):
```
POST /api/auth/login
```

### Authenticated (All Users):
```
POST /api/auth/logout
GET  /api/auth/me
POST /api/auth/change-password
```

### Admin Only:
```
GET    /api/auth/users              # List all users
POST   /api/auth/users              # Create user
DELETE /api/auth/users/{user_id}   # Delete user
PUT    /api/auth/users/{user_id}/toggle-active  # Enable/disable
PUT    /api/auth/users/{user_id}/change-role    # Change role
```

---

## 💻 Frontend Usage

### Check if logged in:
```javascript
if (isAuthenticated()) {
    // User is logged in
}
```

### Check if admin:
```javascript
if (isAdmin()) {
    // Show admin features
}
```

### Make authenticated request:
```javascript
const response = await authFetch(`${API_BASE_URL}/domains`);
```

### Hide/show admin features:
```html
<!-- Only show for admin -->
<div class="admin-only">
    <button>Manage Users</button>
</div>
```

---

## 🔧 Admin Functions

### Create User

```javascript
// Admin can create new users
const response = await authFetch(`${API_BASE_URL}/auth/users`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        username: 'newuser',
        password: 'password123',
        full_name: 'New User',
        role_id: 2  // 1=admin, 2=user
    })
});
```

### Change User Role

```javascript
// Change user to admin
await authFetch(`${API_BASE_URL}/auth/users/5/change-role?role_id=1`, {
    method: 'PUT'
});
```

### Disable User

```javascript
// Toggle user active status
await authFetch(`${API_BASE_URL}/auth/users/5/toggle-active`, {
    method: 'PUT'
});
```

---

## 🌐 Access URLs

Since you're using standard HTTP/HTTPS ports:

- **Frontend:** http://YOUR_SERVER (port 80)
- **Backend API:** http://YOUR_SERVER:8080
- **API Docs:** http://YOUR_SERVER:8080/docs

---

## ⚙️ Configuration

### Port Configuration

In `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "80:80"      # HTTP
    # - "443:443"  # HTTPS (if using SSL)

backend:
  ports:
    - "8080:8080"
```

### For HTTPS:

1. Add SSL certificate to nginx
2. Update frontend config to use HTTPS
3. Change port mapping to 443

---

## 🧪 Testing

### Test Login

```bash
curl -X POST http://YOUR_SERVER:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123"}'
```

**Expected response:**
```json
{
  "token": "long-random-token",
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "role_id": 1,
    "role_name": "admin",
    "is_active": true
  },
  "message": "Login successful"
}
```

### Test Protected Endpoint

```bash
TOKEN="your-token-here"

curl http://YOUR_SERVER:8080/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔒 Security Notes

- Passwords are hashed with bcrypt (cost 12)
- Sessions stored in database
- Token sent via Bearer authentication
- No token expiry (sessions persist until logout)
- Admin cannot delete/disable themselves

---

## 🆘 Troubleshooting

### Cannot login:

1. Check if migration ran:
   ```bash
   docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT * FROM users"
   ```

2. Reset admin password if needed:
   ```bash
   docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor <<EOF
   UPDATE users
   SET password_hash = '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqgdW9E5SC'
   WHERE username = 'admin';
   EOF
   ```

### Session invalid:

1. Check sessions table:
   ```bash
   docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT * FROM sessions"
   ```

2. Clear all sessions:
   ```bash
   docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "DELETE FROM sessions"
   ```

---

## 📝 Summary

**Simplified Authentication:**
- ✅ 3 tables only (roles, users, sessions)
- ✅ 2 roles only (admin, user)
- ✅ Simple login flow
- ✅ Token stored in localStorage
- ✅ Admin can manage users
- ✅ Users can change own password
- ✅ Port 80 for HTTP (not 8888)

**Clean and simple!** 🎉
