# SSL Certificate Monitoring System

A simple SSL certificate monitoring system with authentication.

## Quick Start

### Prerequisites
- Linux server with Docker & Docker Compose
- Ports 80 and 8080 available

### Deploy

```bash
chmod +x start.sh
./start.sh
```

Wait 2-3 minutes, then access:
- **Frontend:** http://YOUR_SERVER (port 80)
- **Login:** admin / Admin@123

## Features

- SSL certificate monitoring
- Automatic scanning every 5 seconds
- Simple authentication (username/password)
- 2 roles: admin (full access), user (limited)
- Bulk domain management
- CSV export
- Real-time dashboard

## Architecture

```
Nginx (port 80) → Backend (FastAPI) → PostgreSQL
                      ↓
                  Scanner (Bash)
```

## Authentication

**Simple system:**
- Login: username + password
- 2 roles: admin, user
- Admin: manage users, full access
- User: view domains, change own password

**Database tables:**
- roles - 2 roles (admin, user)
- users - user accounts
- sessions - login tokens

## Management

```bash
# View logs
docker compose logs -f

# Restart
docker compose restart

# Stop
docker compose down

# Redeploy
docker compose down -v
./start.sh
```

## Default Account

- Username: admin
- Password: Admin@123
- Change password after first login!

## Support

Check logs: docker compose logs -f

---

**Version:** 1.0  
**Port:** 80 (HTTP)
