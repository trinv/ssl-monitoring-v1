# SSL Monitor - Deployment Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Docker & Docker Compose installed
- Port 80 available (or change in docker-compose.yml)
- At least 2GB RAM, 10GB disk space

### Step 1: Clone & Setup
```bash
cd /path/to/ssl-monitoring-v1

# Copy environment template
cp .env.example .env
```

### Step 2: Configure Environment
Edit `.env` file and update these **CRITICAL** values:

```env
# REQUIRED: Generate strong secrets
DB_PASSWORD=<run: openssl rand -base64 32>
JWT_SECRET=<run: openssl rand -base64 64>

# REQUIRED: Set your domain
CORS_ORIGINS=https://yourdomain.com

# OPTIONAL: Adjust if needed
ENVIRONMENT=production
```

### Step 3: Build & Start
```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 4: Verify Installation
```bash
# Test health endpoint
curl http://localhost/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-12-02T...",
  "version": "3.0.0",
  "environment": "production"
}
```

### Step 5: Login & Change Password
```bash
# Login with default credentials
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123456"
  }'

# Response includes token:
{
  "access_token": "eyJ...",
  "user": { "id": 1, "username": "admin", "role": "admin" }
}

# ⚠️ IMPORTANT: Change password immediately!
# (Implementation needed in routes)
```

---

## 🔧 Detailed Configuration

### Environment Variables

#### Database
```env
DB_HOST=postgres              # Container name
DB_PORT=5432                  # PostgreSQL port
DB_NAME=ssl_monitor           # Database name
DB_USER=ssluser              # Database user
DB_PASSWORD=<STRONG_PASSWORD> # ⚠️ CHANGE THIS
DB_POOL_SIZE=20              # Connection pool size
DB_POOL_MAX_OVERFLOW=10      # Max overflow
```

#### Backend
```env
BACKEND_HOST=0.0.0.0         # Bind to all interfaces
BACKEND_PORT=8080            # Internal port
BACKEND_WORKERS=4            # Uvicorn workers
BACKEND_LOG_LEVEL=info       # Logging level
```

#### Security
```env
JWT_SECRET=<STRONG_SECRET>   # ⚠️ CHANGE THIS (min 32 chars)
JWT_ALGORITHM=HS256          # Don't change
JWT_EXPIRATION_HOURS=24      # Token lifetime
```

#### Scanner
```env
SCANNER_CONCURRENCY=20       # Concurrent scans
SCANNER_TIMEOUT=15           # Timeout per domain (seconds)
SCANNER_RETRY=3              # Retry attempts
SCANNER_BATCH_SIZE=1000      # Domains per batch
SCANNER_VERIFY_SSL=false     # SSL verification (false for monitoring)
```

#### CORS
```env
CORS_ORIGINS=https://domain1.com,https://domain2.com
ALLOW_CREDENTIALS=true
```

---

## 🏗️ Architecture

```
┌─────────────┐
│   Nginx     │ :80 (Frontend + Reverse Proxy)
│  (Alpine)   │
└──────┬──────┘
       │
       ├─────► /          → Static Files (Frontend)
       ├─────► /api/*     → Backend (FastAPI)
       └─────► /health    → Health Check
              │
┌─────────────▼──────────┐
│   Backend (FastAPI)    │ :8080
│   - Authentication     │
│   - Domain Management  │
│   - Scan Triggering    │
└─────────┬──────────────┘
          │
          ├──────┐
          │      │
┌─────────▼───┐  ┌─────▼──────────┐
│  PostgreSQL │  │    Scanner     │
│  (15-alpine)│  │  (Async SSL)   │
│             │  │                │
│  - Users    │  │  - Auto Scan   │
│  - Domains  │  │  - Concurrency │
│  - Certs    │  │  - Retry Logic │
└─────────────┘  └────────────────┘
```

---

## 📊 Service Details

### Nginx (Port 80)
- **Purpose**: Reverse proxy, static file serving, rate limiting
- **Health**: Check with `curl http://localhost/health`
- **Logs**: `docker-compose logs nginx`
- **Config**: `nginx/nginx.conf`

### Backend (Port 8080 internal)
- **Purpose**: API endpoints, authentication, business logic
- **Health**: `curl http://localhost:8080/health` (internal)
- **Logs**: `docker-compose logs backend`
- **Workers**: 4 (configurable via `BACKEND_WORKERS`)

### Scanner
- **Purpose**: Automated SSL certificate scanning
- **Schedule**: Continuous (30s interval)
- **Batch**: 1000 domains per batch
- **Concurrency**: 20 simultaneous scans
- **Logs**: `docker-compose logs scanner`

### PostgreSQL (Port 5432 internal)
- **Purpose**: Data persistence
- **Version**: 15-alpine
- **Health**: Auto-checked by docker-compose
- **Backup**: See backup section below

---

## 🔐 Security Hardening

### 1. SSL/TLS (HTTPS)

**Enable HTTPS:**
```bash
# 1. Get SSL certificate (Let's Encrypt recommended)
certbot certonly --standalone -d yourdomain.com

# 2. Copy certificates
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/

# 3. Update nginx.conf (uncomment HTTPS block)
# 4. Update docker-compose.yml to expose port 443
# 5. Restart
docker-compose restart nginx
```

### 2. Firewall Rules
```bash
# Allow only necessary ports
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw deny 8080/tcp  # Backend (internal only)
ufw deny 5432/tcp  # PostgreSQL (internal only)
ufw enable
```

### 3. Change Default Passwords
```bash
# Admin password (in database)
# Login to PostgreSQL:
docker-compose exec postgres psql -U ssluser -d ssl_monitor

# Update password hash:
UPDATE users
SET password_hash = '<new_bcrypt_hash>'
WHERE username = 'admin';
```

### 4. Environment Security
```bash
# Restrict .env file permissions
chmod 600 .env

# Never commit .env to git
echo ".env" >> .gitignore
```

---

## 📈 Monitoring & Logs

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f scanner
docker-compose logs -f nginx

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Health Checks
```bash
# Overall health
curl http://localhost/health

# Database check
docker-compose exec postgres pg_isready -U ssluser

# Backend check
curl http://localhost/ready
```

### Resource Usage
```bash
# Container stats
docker stats

# Disk usage
docker system df
```

---

## 🔄 Backup & Restore

### Database Backup
```bash
# Create backup
docker-compose exec postgres pg_dump -U ssluser ssl_monitor > backup_$(date +%Y%m%d).sql

# Automated daily backup (cron)
0 2 * * * docker-compose exec postgres pg_dump -U ssluser ssl_monitor > /backups/ssl_monitor_$(date +\%Y\%m\%d).sql
```

### Restore Database
```bash
# Restore from backup
docker-compose exec -T postgres psql -U ssluser ssl_monitor < backup_20241202.sql
```

---

## 🔧 Troubleshooting

### Issue: "Connection refused"
```bash
# Check if all containers are running
docker-compose ps

# Restart specific service
docker-compose restart backend

# Rebuild if needed
docker-compose up -d --build backend
```

### Issue: "Database connection failed"
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify environment variables
docker-compose exec backend env | grep DB_

# Test connection manually
docker-compose exec postgres psql -U ssluser -d ssl_monitor -c "SELECT 1"
```

### Issue: "Scanner not scanning"
```bash
# Check scanner logs
docker-compose logs scanner

# Verify active domains exist
docker-compose exec postgres psql -U ssluser -d ssl_monitor \
  -c "SELECT COUNT(*) FROM domains WHERE is_active = true"

# Restart scanner
docker-compose restart scanner
```

### Issue: "Rate limit exceeded"
```bash
# Adjust rate limits in nginx.conf
# Increase values in limit_req_zone directives
# Then restart nginx
docker-compose restart nginx
```

---

## ⚡ Performance Tuning

### Database
```env
# Increase pool size for high traffic
DB_POOL_SIZE=50
DB_POOL_MAX_OVERFLOW=20
```

### Backend
```env
# Increase workers for more concurrent requests
BACKEND_WORKERS=8
```

### Scanner
```env
# Increase concurrency for faster scanning
SCANNER_CONCURRENCY=50
SCANNER_BATCH_SIZE=2000
```

---

## 🔄 Update & Maintenance

### Update Code
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Clean everything
docker system prune -a --volumes
```

---

## 📞 Support

### Logs Location
- Nginx: `docker-compose logs nginx`
- Backend: `docker-compose logs backend`
- Scanner: `docker-compose logs scanner`
- Database: `docker-compose logs postgres`

### Common Commands
```bash
# Stop all services
docker-compose stop

# Start all services
docker-compose start

# Restart specific service
docker-compose restart <service>

# View running containers
docker-compose ps

# Remove all containers
docker-compose down

# Remove all including volumes
docker-compose down -v
```

---

## ✅ Production Checklist

Before deploying to production:

- [ ] Changed `DB_PASSWORD` (min 32 chars)
- [ ] Changed `JWT_SECRET` (min 64 chars)
- [ ] Updated `CORS_ORIGINS` to your domain
- [ ] Changed default admin password
- [ ] Enabled HTTPS (SSL certificates installed)
- [ ] Configured firewall rules
- [ ] Set up automated backups
- [ ] Configured monitoring/alerts
- [ ] Tested all API endpoints
- [ ] Reviewed nginx rate limits
- [ ] Set `ENVIRONMENT=production` in .env
- [ ] Restricted .env file permissions (chmod 600)
- [ ] Added .env to .gitignore
- [ ] Documented custom configurations
- [ ] Tested disaster recovery plan

---

**Version:** 3.0.0
**Last Updated:** 2024-12-02
**Support:** Check CHANGELOG.md for updates
