# 🔐 SSL Certificate Monitoring System

[![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

A comprehensive SSL certificate monitoring system with user authentication, built with FastAPI, PostgreSQL, and AdminLTE.

![Dashboard Screenshot](https://via.placeholder.com/800x400?text=SSL+Monitor+Dashboard)

## ✨ Features

- 🔐 **User Authentication** - Role-based access control (Admin, User, Viewer)
- 📊 **Real-time Dashboard** - Monitor SSL certificate status at a glance
- 🔍 **Automatic Scanning** - Continuous monitoring every 5 seconds
- 📝 **Domain Management** - Bulk add, edit, and delete domains
- 📈 **History Tracking** - Track SSL status changes over time
- 📥 **CSV Export** - Export monitoring data
- 🛡️ **Security** - Bcrypt password hashing, session management, audit logs
- 🎨 **Modern UI** - Responsive AdminLTE v2 interface

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- Ports: 8888 (frontend), 8080 (backend), 5432 (database)

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/ssl-monitoring.git
cd ssl-monitoring

# Deploy everything
chmod +x deploy.sh
./deploy.sh
```

That's it! The script will:
- ✅ Build all Docker images
- ✅ Start all services
- ✅ Create database schema
- ✅ Set up authentication
- ✅ Create default admin user

### Access

- **Frontend:** http://localhost:8888
- **API Docs:** http://localhost:8080/docs
- **Default Login:** admin / Admin@123

⚠️ **Change the default password after first login!**

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[Authentication Setup](AUTH_SETUP.md)** - Auth system configuration
- **[API Documentation](http://localhost:8080/docs)** - Interactive API docs (when running)

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│   Frontend  │─────▶│   Backend   │─────▶│  PostgreSQL  │
│  (Nginx)    │      │  (FastAPI)  │      │              │
│  Port 8888  │      │  Port 8080  │      │  Port 5432   │
└─────────────┘      └─────────────┘      └──────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   Scanner   │
                     │   (Bash)    │
                     └─────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python web framework)
- PostgreSQL (Database)
- asyncpg (Async database driver)
- bcrypt (Password hashing)

**Frontend:**
- AdminLTE v2 (Admin template)
- Bootstrap 4 (UI framework)
- jQuery (DOM manipulation)

**Scanner:**
- Bash + OpenSSL (SSL scanning)
- curl (HTTP/HTTPS testing)

## 🔐 Security Features

- **Password Security:** Bcrypt hashing (cost factor 12)
- **Account Protection:** Auto-lock after 5 failed attempts
- **Session Management:** Secure tokens with 24-hour expiry
- **Audit Logging:** All auth events tracked
- **RBAC:** Role-based access with 15 granular permissions

## 👥 User Roles

| Role   | Permissions                                    |
|--------|------------------------------------------------|
| Admin  | Full access, user management, all operations  |
| User   | View, add, edit, delete domains, trigger scans|
| Viewer | View domains, SSL status, export data         |

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

### Domain Management
- `GET /api/domains` - List domains (paginated)
- `POST /api/domains` - Add domain
- `POST /api/domains/bulk` - Bulk add domains
- `DELETE /api/domains/{id}` - Delete domain

### SSL Scanning
- `POST /api/scan/trigger` - Trigger full scan
- `POST /api/scan/domains` - Scan specific domains

### Dashboard
- `GET /api/dashboard/summary` - Get statistics
- `GET /api/export/csv` - Export to CSV

## 🛠️ Management

### View Logs
```bash
docker compose logs -f
```

### Restart Services
```bash
docker compose restart
```

### Stop Services
```bash
docker compose down
```

### Backup Database
```bash
docker exec ssl-monitoring-postgres pg_dump -U ssluser ssl_monitor > backup.sql
```

### Restore Database
```bash
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < backup.sql
```

## 🐛 Troubleshooting

### Backend won't start
```bash
docker compose logs backend
docker compose restart backend
```

### Database connection failed
```bash
docker compose restart postgres
# Wait 30 seconds
docker compose restart backend
```

### Cannot login
```bash
# Verify admin user exists
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT username FROM users WHERE username='admin'"

# If not found, run migrations manually
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql
```

## 📈 Production Deployment

For production use:

1. **Change passwords** in `docker-compose.yml`
2. **Configure CORS** in `backend/main.py` with your domain
3. **Set up HTTPS** with nginx + Let's Encrypt
4. **Enable firewall** (block port 5432 from external access)
5. **Set up backups** (automated daily backups)

See [Deployment Guide](DEPLOYMENT_GUIDE.md) for details.

## 🔄 Updates

Pull latest changes and rebuild:

```bash
git pull
docker compose build
docker compose up -d
```

## 📝 License

Proprietary - All rights reserved.

This project is developed for VNNIC/Namestar.

## 🤝 Contributing

This is a private project. Contact the repository owner for collaboration.

## 📞 Support

For issues or questions:

1. Check the [Deployment Guide](DEPLOYMENT_GUIDE.md)
2. View logs: `docker compose logs -f`
3. Check service status: `docker compose ps`

## 🎯 Roadmap

- [ ] Email notifications for expiring certificates
- [ ] Telegram/Slack integration
- [ ] Multi-language support
- [ ] Certificate renewal automation
- [ ] Advanced reporting

## ⭐ Credits

Developed with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [AdminLTE](https://adminlte.io/)
- [Docker](https://www.docker.com/)

---

**Made with ❤️ for SSL monitoring**

**Version:** 1.0.0
**Last Updated:** 2025-01-29
