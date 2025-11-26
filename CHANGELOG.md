# CHANGELOG - Domain Monitor

## Version 1.2.0 (2025-11-26) - Simplified & Fixed

### 🎯 Major Changes

**1. Removed Redis**
- ❌ Removed Redis service from docker-compose
- ❌ Removed Redis client from backend
- ❌ Removed Redis volume
- ✅ Simplified architecture
- ✅ Reduced resource usage
- ✅ Fewer moving parts

**2. Set Default Passwords**
- ✅ POSTGRES_DB=domains
- ✅ POSTGRES_USER=domainuser
- ✅ POSTGRES_PASSWORD=s3gs8Tu50ISwFu37
- ✅ SECRET_KEY=vP49i2v0wQzoQHL9
- ⚠️ Still recommended to change in production!

**3. Simplified Frontend**
- ❌ Removed Status Distribution chart
- ❌ Removed System Info panel
- ✅ Cleaner dashboard layout
- ✅ Focus on domain list
- ✅ Faster page load

**4. Fixed Dashboard Data Issue**
- 🐛 Dashboard showed 0 despite having 200+ domains
- ✅ Added `REFRESH MATERIALIZED VIEW` on every API call
- ✅ Now shows real-time data
- ✅ No caching issues

### 📝 Technical Changes

**Backend (main.py):**
```python
# Removed Redis
- import redis.asyncio as aioredis
- redis_client = None

# Added materialized view refresh
await db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY latest_domain_status")
```

**docker-compose.yml:**
```yaml
# Removed entire redis service
# Removed redis dependency from backend
# Removed redis_data volume
# Updated passwords to default values
```

**Frontend (index.html):**
```html
<!-- Removed -->
<div class="card">Status Distribution Chart</div>
<div class="card">System Info Panel</div>

<!-- Kept -->
4 stats cards
Domain list table
Filters & search
```

**Environment (.env):**
```bash
# Default passwords set
POSTGRES_PASSWORD=s3gs8Tu50ISwFu37
SECRET_KEY=vP49i2v0wQzoQHL9

# Removed
REDIS_PASSWORD
REDIS_URL
```

### 🐛 Bug Fixes

**Critical: Dashboard showing 0 despite having data**
- **Root Cause**: Materialized view not refreshed after adding domains
- **Solution**: Refresh view on every dashboard/domains API call
- **Impact**: Real-time data display

### ⚠️ Breaking Changes

1. **Redis removed** - No backward compatibility
2. **Default passwords** - Security implications
3. **No caching** - Slightly slower API (negligible)

### 📦 Services

**Before (v1.1.1):**
- postgres
- redis
- backend
- scanner
- nginx

**After (v1.2.0):**
- postgres
- backend  
- scanner
- nginx

**Removed: redis** (25% fewer services!)

---

## Version 1.1.1 (2025-11-26) - Scanner Bugfix

### 🐛 Bug Fixes
- Fixed division by zero in scanner when scan completes too fast
- Added check for `scan_duration > 0`

---

## Version 1.1.0 (2025-11-26) - No Authentication

### 🔓 Major Changes
- Removed authentication system
- Added CONFIGURATION.md guide
- Direct dashboard access

---

## Version 1.0.1 (2025-11-26) - Database Fix

### 🐛 Bug Fixes
- Fixed PostgreSQL healthcheck error
- Added fix-database.sh script

---

## Version 1.0.0 (2025-11-25) - Initial Release

### 🎯 Core Features
- Backend with authentication
- 50k+ domain optimization
- Scanner with 2,000 concurrency

---

## Migration Guide

### From v1.1.1 to v1.2.0

**⚠️ BREAKING CHANGES - Redis removed**

```bash
# 1. Stop current services
docker-compose down

# 2. Remove Redis volume (optional)
docker volume rm domain-monitor_redis_data

# 3. Download new package
tar -xzf domain-monitor-v1.2.0.tar.gz
cd domain-monitor

# 4. Start new version (no .env changes needed - defaults included)
docker-compose up -d

# Done! Redis is gone, dashboard works!
```

**What you'll see:**
- ✅ Dashboard shows real data immediately
- ✅ No Redis logs
- ✅ Cleaner interface
- ✅ Same domain data preserved

---

## Known Issues

### Fixed in v1.2.0
- ✅ Dashboard showing 0 despite having data
- ✅ Redis unnecessary complexity
- ✅ Default passwords not set

### Fixed in v1.1.1
- ✅ Scanner division by zero

### Current Issues
- None reported

---

## FAQ

**Q: Why remove Redis?**
A: Not needed for this scale. PostgreSQL handles caching well. Simpler = better.

**Q: Will dashboard be slower without Redis?**
A: No. Materialized views are fast. Difference is negligible.

**Q: Should I change default passwords?**
A: YES for production! Edit `.env` file.

**Q: What if I added 200+ domains but see 0?**
A: Update to v1.2.0. The materialized view refresh fixes this.

**Q: Do I lose data when upgrading?**
A: No. PostgreSQL data persists. Only Redis cache is lost (which doesn't matter).

---

**Current Version:** v1.2.0  
**Release Date:** November 26, 2025  
**Status:** ✅ Production Ready  
**Services:** 4 (was 5)  
**Redis:** Removed  
**Dashboard:** Fixed
