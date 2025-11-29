# 🔧 Fix Login Error

## ❌ Current Error

```
relation "users" does not exist
Network error. Please try again.
```

---

## ✅ Solution (Choose ONE)

### 🎯 Option 1: Double-click BAT file (Easiest!)

**Just double-click this file:**
```
create_auth_tables.bat
```

It will:
- ✅ Check if PostgreSQL is running
- ✅ Create auth tables
- ✅ Create admin user
- ✅ Verify everything

### 🎯 Option 2: PowerShell

```powershell
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql
```

### 🎯 Option 3: CMD

```cmd
type database\simple_auth_migration.sql | docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor
```

---

## 🧪 After Running, Test:

1. Open: **http://YOUR_SERVER**
2. Login:
   - Username: **admin**
   - Password: **Admin@123**
3. Should work! ✅

---

## 📝 What Gets Created

- **roles** table → admin, user
- **users** table → user accounts
- **sessions** table → login sessions
- **admin user** → admin/Admin@123

---

## 🆘 Still Not Working?

See: **[RUN_THIS_NOW.md](RUN_THIS_NOW.md)** for detailed troubleshooting.

---

**Quick Fix:** Just run `create_auth_tables.bat` 🚀
