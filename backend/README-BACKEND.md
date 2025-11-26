# Backend API - Troubleshooting

## Common Issues & Solutions

### Issue 1: Backend won't start

**Symptoms:**
```
docker-compose logs backend
# Shows connection errors or crashes
```

**Solutions:**

1. **Check PostgreSQL is ready:**
```bash
docker-compose ps
# postgres should show "Up (healthy)"

# Test connection
docker-compose exec postgres psql -U ssluser -d ssl_monitor -c "SELECT 1"
```

2. **Check environment variables:**
```bash
docker-compose exec backend env | grep DB_
# Should show:
# DB_HOST=postgres
# DB_PORT=5432
# DB_NAME=ssl_monitor
# DB_USER=ssluser
# DB_PASSWORD=SSL@Pass123
```

3. **Restart backend:**
```bash
docker-compose restart backend
docker-compose logs -f backend
```

### Issue 2: "Connection refused" errors

**Cause:** Backend starting before PostgreSQL is ready

**Solution:** The entrypoint.sh now waits for PostgreSQL (up to 60 seconds)

### Issue 3: Import errors

**Check Python dependencies:**
```bash
docker-compose exec backend pip list
# Should show:
# fastapi        0.104.1
# uvicorn        0.24.0
# asyncpg        0.29.0
# pydantic       2.5.0
```

### Issue 4: Port already in use

**Check port 8080:**
```bash
netstat -tlnp | grep :8080
# or
lsof -i :8080
```

**Solution:**
```bash
# Kill process using port
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8081:8080"  # Use 8081 instead
```

## Manual Testing

### Test backend locally:

```bash
# Enter container
docker-compose exec backend bash

# Test Python syntax
python -m py_compile main.py

# Test imports
python -c "from main import app; print('OK')"

# Test database connection
python -c "
import asyncio
import asyncpg
import os

async def test():
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    result = await conn.fetchval('SELECT 1')
    print(f'Connection OK: {result}')
    await conn.close()

asyncio.run(test())
"
```

### Test API endpoints:

```bash
# Root endpoint
curl http://localhost:8080/

# Health check
curl http://localhost:8080/health

# Dashboard summary
curl http://localhost:8080/api/dashboard/summary

# Domains list
curl http://localhost:8080/api/domains
```

## Logs

### View logs:
```bash
# All logs
docker-compose logs backend

# Follow logs
docker-compose logs -f backend

# Last 50 lines
docker-compose logs backend --tail=50
```

### Expected startup logs:
```
Starting application...
Connecting to PostgreSQL at postgres:5432/ssl_monitor
✅ Successfully connected to PostgreSQL
FastAPI application started
API documentation available at: /docs
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## Configuration

### Environment variables (.env):
```bash
DB_HOST=postgres
DB_PORT=5432
DB_NAME=ssl_monitor
DB_USER=ssluser
DB_PASSWORD=SSL@Pass123
```

### Update configuration:
```bash
# Edit .env
nano .env

# Restart backend
docker-compose restart backend
```

## Rebuild Backend

If you've made changes:

```bash
# Rebuild without cache
docker-compose build --no-cache backend

# Restart
docker-compose up -d backend

# Check logs
docker-compose logs -f backend
```

## Complete Reset

If nothing works:

```bash
# Stop all
docker-compose down

# Remove volumes (CAUTION: deletes data!)
docker-compose down -v

# Rebuild everything
docker-compose up -d --build

# Check status
docker-compose ps
docker-compose logs -f backend
```
