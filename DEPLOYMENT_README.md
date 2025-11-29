# 🚀 SSL Monitor - Quick Deployment Guide

## 📋 Prerequisites

- Linux server with Docker installed
- Docker Compose v2+
- Ports 80 and 8080 available

## ⚡ One-Command Deployment

```bash
# Clone or download source code to your Linux server
# Then run:

chmod +x start.sh
./start.sh
```

That's it! The script will:
1. ✅ Check Docker & Docker Compose
2. ✅ Clean up old containers (`docker compose down -v`)
3. ✅ Build all Docker images
4. ✅ Start all services
5. ✅ Wait for PostgreSQL & Backend
6. ✅ Create database schema (domains + auth)
7. ✅ Verify everything is working
8. ✅ Show access information

**Time:** 2-3 minutes

---

## 🌐 After Deployment

You'll see:

```
🎉 Deployment Complete!

📍 Access Information:
   Frontend:  http://YOUR_SERVER_IP
   Backend:   http://YOUR_SERVER_IP:8080
   API Docs:  http://YOUR_SERVER_IP:8080/docs

🔐 Login Credentials:
   Username: admin
   Password: Admin@123

⚠️  IMPORTANT: Change admin password after first login!
```

---

## 🔐 Authentication

### Simple Authentication System:
- **2 roles:** admin (full access), user (limited)
- **Login:** Username + password
- **Sessions:** Token-based, stored in database
- **Admin can:**
  - Create/delete users
  - Change user roles
  - Enable/disable users
- **Users can:**
  - View domains
  - Change own password

---

## 📊 Service Architecture

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│   Nginx     │─────▶│   Backend   │─────▶│  PostgreSQL  │
│  Port 80    │      │  Port 8080  │      │              │
└─────────────┘      └─────────────┘      └──────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   Scanner   │
                     └─────────────┘
```

---

## 🛠️ Management Commands

### View Logs
```bash
docker compose logs -f              # All services
docker compose logs -f backend      # Backend only
docker compose logs -f postgres     # Database only
docker compose logs -f scanner      # Scanner only
```

### Service Control
```bash
docker compose ps                   # Check status
docker compose restart              # Restart all
docker compose restart backend      # Restart backend only
docker compose stop                 # Stop all
docker compose start                # Start all
```

### Complete Cleanup
```bash
docker compose down -v              # Stop and remove everything
```

### Redeploy
```bash
docker compose down -v              # Clean up
./start.sh                          # Deploy again
```

---

## 🔧 Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. Database not ready - wait 30s and restart
docker compose restart backend

# 2. Port 8080 already in use
# Change port in docker-compose.yml
```

### Frontend shows blank page

```bash
# Check backend health
curl http://localhost:8080/health

# Should return: {"status":"healthy","database":"ok"}
```

### Cannot login

```bash
# Check if auth tables exist
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "\dt"

# Should see: roles, users, sessions

# If not, run migration manually:
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/simple_auth_migration.sql
```

### Database errors

```bash
# Check PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres

# Wait 30 seconds then restart backend
sleep 30
docker compose restart backend
```

---

## 📁 Database Backup & Restore

### Backup

```bash
# Create backup
docker exec ssl-monitoring-postgres pg_dump -U ssluser ssl_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# Or with compression
docker exec ssl-monitoring-postgres pg_dump -U ssluser ssl_monitor | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore

```bash
# Stop backend first
docker compose stop backend

# Restore from backup
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < backup.sql

# Or from compressed
gunzip < backup.sql.gz | docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor

# Start backend
docker compose start backend
```

---

## 🔐 Security Recommendations

### After First Login:

1. **Change admin password**
   - Login as admin
   - Go to profile
   - Change password

2. **Create regular users** (admin only)
   ```bash
   # Via API or frontend
   # POST /api/auth/users
   {
     "username": "user1",
     "password": "secure_password",
     "full_name": "User One",
     "role_id": 2  # 2 = user, 1 = admin
   }
   ```

3. **Firewall configuration**
   ```bash
   # Allow only ports 80 and 8080
   ufw allow 80/tcp
   ufw allow 8080/tcp
   ufw enable
   ```

4. **Enable HTTPS** (Production)
   - Use Let's Encrypt with certbot
   - Configure nginx with SSL
   - Redirect HTTP to HTTPS

---

## 📈 Monitoring

### Check Service Health

```bash
# Backend health
curl http://localhost:8080/health

# Database connection
docker exec ssl-monitoring-postgres pg_isready -U ssluser -d ssl_monitor

# Scanner status
docker compose logs scanner | tail -20
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

---

## 🔄 Updates

### Pull Latest Changes

```bash
# If using Git
git pull

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
```

### Database Migration (if needed)

```bash
# Run new migration
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/new_migration.sql
```

---

## 📝 File Structure

```
ssl-monitoring/
├── start.sh                    # Main deployment script
├── docker-compose.yml          # Docker services config
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── auth/                   # Auth module (simple)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.html              # Dashboard
│   ├── login.html              # Login page
│   ├── js/
│   │   ├── auth.js             # Auth logic (use simple version)
│   │   └── ...
│   └── css/
├── database/
│   ├── init.sql                # Domain tables
│   └── simple_auth_migration.sql  # Auth tables
└── scanner/
    └── scanner.sh              # SSL scanner
```

---

## ✅ Deployment Checklist

After running `./start.sh`:

- [ ] All 4 services running (`docker compose ps`)
- [ ] Backend health check passes
- [ ] Can access frontend (http://YOUR_SERVER)
- [ ] Login page appears
- [ ] Can login with admin/Admin@123
- [ ] Dashboard loads successfully
- [ ] Can add a test domain
- [ ] Scanner is working (check logs)
- [ ] Changed admin password

---

## 🆘 Getting Help

### Logs to Check

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f scanner
docker compose logs -f nginx
```

### Common Commands

```bash
# Full restart
docker compose restart

# Rebuild after code changes
docker compose build backend
docker compose up -d backend

# Complete redeploy
docker compose down -v
./start.sh
```

---

## 🎉 That's It!

Your SSL monitoring system should be running and accessible at:
- **http://YOUR_SERVER** (login: admin/Admin@123)

**Happy monitoring!** 🔐✨
