# 🚀 SSL Monitor - Deployment Guide

## 📦 Deployment from GitHub

This guide helps you deploy the SSL monitoring system on a new Docker environment after cloning from GitHub.

---

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git
- Minimum 2GB RAM
- Ports available: 8888 (frontend), 8080 (backend), 5432 (postgres)

---

## 🔧 Step-by-Step Deployment

### Step 1: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/YOUR_USERNAME/ssl-monitoring.git
cd ssl-monitoring

# Or if already cloned, just navigate to directory
cd /path/to/ssl-monitoring
```

### Step 2: Configure Environment (Optional)

If you want to change default settings, edit `docker-compose.yml`:

```yaml
# Backend environment
environment:
  DB_HOST: postgres
  DB_PORT: 5432
  DB_NAME: ssl_monitor
  DB_USER: ssluser
  DB_PASSWORD: SSL@Pass123  # Change if needed
```

### Step 3: Deploy Everything

Run the automated deployment script:

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
1. ✅ Build all Docker images
2. ✅ Start all services
3. ✅ Wait for PostgreSQL to be ready
4. ✅ Create database schema
5. ✅ Create authentication tables
6. ✅ Insert default admin user
7. ✅ Verify deployment

**Expected time:** 2-3 minutes

---

## 🎯 What Gets Deployed

### Services Started:
- **PostgreSQL** - Database (port 5432)
- **Backend** - FastAPI application (port 8080)
- **Frontend** - Nginx web server (port 8888)
- **Scanner** - SSL certificate scanner (background)

### Database Tables Created:
- `domains` - Domain list
- `ssl_scan_results` - Scan history
- `users` - User accounts
- `roles` - User roles (admin, user, viewer)
- `permissions` - Granular permissions
- `role_permissions` - Role-permission mappings
- `sessions` - User sessions
- `audit_logs` - Audit trail

### Default Admin Account:
- **Username:** `admin`
- **Password:** `Admin@123`
- **⚠️ IMPORTANT:** Change password after first login!

---

## 🌐 Access the Application

After deployment completes:

1. **Open browser:** http://YOUR_SERVER_IP:8888
2. **You'll be redirected to login page**
3. **Login with:** admin / Admin@123
4. **Change your password** immediately
5. **Start monitoring** your SSL certificates!

---

## 🔍 Verify Deployment

### Check All Services Running

```bash
docker compose ps
```

**Expected output:**
```
NAME                    STATUS          PORTS
ssl-monitor-backend     Up              0.0.0.0:8080->8080/tcp
ssl-monitor-frontend    Up              0.0.0.0:8888->80/tcp
ssl-monitoring-postgres Up              5432/tcp
ssl-monitor-scanner     Up
```

### Check Backend Health

```bash
curl http://localhost:8080/health
```

**Expected response:**
```json
{"status":"healthy","database":"ok"}
```

### Check Database Tables

```bash
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "\dt"
```

**Expected output:** Should show 8 tables

### Check Admin User Exists

```bash
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT username, email FROM users WHERE username='admin'"
```

**Expected output:**
```
 username |         email
----------+------------------------
 admin    | admin@sslmonitor.local
```

---

## 📊 View Logs

### All services:
```bash
docker compose logs -f
```

### Backend only:
```bash
docker compose logs -f backend
```

### PostgreSQL only:
```bash
docker compose logs -f postgres
```

### Scanner only:
```bash
docker compose logs -f scanner
```

---

## 🛠️ Management Commands

### Start Services

```bash
docker compose up -d
```

### Stop Services

```bash
docker compose down
```

### Restart Services

```bash
docker compose restart
```

### Rebuild Backend (after code changes)

```bash
docker compose build backend
docker compose up -d backend
```

### View Service Status

```bash
docker compose ps
```

---

## 🔧 Troubleshooting

### Issue: Backend won't start

**Check logs:**
```bash
docker compose logs backend
```

**Common causes:**
- Database not ready yet (wait 30 seconds and retry)
- Port 8080 already in use
- Database connection failed

**Solution:**
```bash
docker compose restart backend
```

### Issue: Frontend shows blank page

**Check if backend is running:**
```bash
curl http://localhost:8080/health
```

**Check browser console** for errors

**Clear browser cache:** Ctrl+Shift+R

### Issue: Cannot login

**Verify database migration ran:**
```bash
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT COUNT(*) FROM users"
```

**If returns error, run migration manually:**
```bash
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/init.sql
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql
```

### Issue: Database connection errors

**Check PostgreSQL is running:**
```bash
docker compose ps postgres
```

**Check credentials in docker-compose.yml match**

**Restart PostgreSQL:**
```bash
docker compose restart postgres
```

---

## 🔐 Security Recommendations

### After Deployment:

1. **Change Admin Password**
   - Login as admin
   - Go to profile settings
   - Change password to a strong one

2. **Update Database Password**
   ```bash
   # Edit docker-compose.yml
   # Change DB_PASSWORD to a secure password
   # Then rebuild:
   docker compose down
   docker compose up -d
   ```

3. **Configure Firewall**
   ```bash
   # Only allow ports 8888 (frontend) and optionally 8080 (API)
   # Block port 5432 (PostgreSQL) from external access
   ```

4. **Enable HTTPS** (Production)
   - Use nginx with SSL certificate
   - Configure Let's Encrypt
   - Update frontend to use HTTPS

5. **Backup Database**
   ```bash
   docker exec ssl-monitoring-postgres pg_dump -U ssluser ssl_monitor > backup.sql
   ```

---

## 📈 Production Configuration

### For Production Deployment:

1. **Update CORS Settings** (`backend/main.py`):
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific domain
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Use Environment Variables:**
   ```bash
   # Create .env file
   DB_PASSWORD=your_secure_password
   SECRET_KEY=your_secret_key
   ```

3. **Set Up SSL/TLS:**
   - Configure nginx with SSL certificate
   - Use Let's Encrypt for free certificates
   - Redirect HTTP to HTTPS

4. **Configure Backup:**
   - Automated daily backups
   - Offsite backup storage
   - Test restore process

5. **Monitoring:**
   - Set up application monitoring
   - Configure alerts
   - Log aggregation

---

## 🔄 Update / Upgrade

### Pull Latest Changes

```bash
git pull origin main
docker compose build
docker compose up -d
```

### Database Migrations

If new migrations are added:

```bash
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/migrations/YYYY-MM-DD_migration_name.sql
```

---

## 📞 Support

### Useful Commands Summary

```bash
# Full deployment
./deploy.sh

# Check status
docker compose ps

# View logs
docker compose logs -f

# Restart all
docker compose restart

# Stop all
docker compose down

# Backup database
docker exec ssl-monitoring-postgres pg_dump -U ssluser ssl_monitor > backup.sql

# Restore database
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < backup.sql

# Access PostgreSQL CLI
docker exec -it ssl-monitoring-postgres psql -U ssluser -d ssl_monitor
```

---

## ✅ Deployment Checklist

After deployment, verify:

- [ ] All 4 services are running (`docker compose ps`)
- [ ] Backend health check passes (`curl http://localhost:8080/health`)
- [ ] Database has 8 tables
- [ ] Admin user exists
- [ ] Can access frontend at port 8888
- [ ] Redirects to login page
- [ ] Can login with admin/Admin@123
- [ ] Dashboard loads successfully
- [ ] Can add a test domain
- [ ] Scanner is working (check logs)
- [ ] Changed admin password

---

## 🎉 Success!

If all checks pass, your SSL monitoring system is ready to use!

**Default Access:**
- **URL:** http://YOUR_SERVER_IP:8888
- **Login:** admin / Admin@123
- **API Docs:** http://YOUR_SERVER_IP:8080/docs

**Remember to:**
1. Change the default admin password
2. Create additional user accounts as needed
3. Configure production settings for security
4. Set up regular backups

Happy monitoring! 🔐✨
