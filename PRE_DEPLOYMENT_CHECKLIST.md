# Pre-Deployment Checklist

## ✅ Files Verification

### Backend Files

- [x] `backend/auth/__init__.py` - Package init file
- [x] `backend/auth/models.py` - Pydantic models (uses EmailStr)
- [x] `backend/auth/utils.py` - Password hashing, token generation
- [x] `backend/auth/dependencies.py` - Auth dependencies with get_db_pool()
- [x] `backend/auth/routes.py` - Auth endpoints
- [x] `backend/main.py` - Includes auth routes
- [x] `backend/Dockerfile` - Copies auth/ directory
- [x] `backend/requirements.txt` - Includes bcrypt + email-validator

### Frontend Files

- [x] `frontend/login.html` - Login page with AdminLTE styling
- [x] `frontend/js/auth.js` - Authentication logic
- [x] `frontend/index.html` - Immediate auth check in <head>

### Database Files

- [x] `database/auth_migration.sql` - Complete schema
- [x] `database/run_auth_migration.sh` - Migration script

## ✅ Import Statements Fixed

### backend/auth/routes.py
```python
# ❌ BEFORE (WRONG)
from database import get_db_pool

# ✅ AFTER (CORRECT)
from auth.dependencies import get_current_user, require_permission, require_role, get_db_pool
```

### backend/auth/dependencies.py
```python
# ✅ CORRECT
async def get_db_pool():
    """Get database pool from main module"""
    import main
    return main.db_pool
```

## ✅ Dependencies Added

### backend/requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
asyncpg==0.29.0
pydantic==2.5.0
python-multipart==0.0.6
requests==2.31.0
bcrypt==4.1.2          # ✅ Added for password hashing
email-validator==2.1.0  # ✅ Added for EmailStr validation
```

## ✅ Dockerfile Updated

### backend/Dockerfile
```dockerfile
# Copy application files
COPY main.py .
COPY auth/ ./auth/    # ✅ Added - copies entire auth module
COPY entrypoint.sh .
```

## ✅ Frontend Auth Protection

### frontend/index.html
```html
<head>
    <!-- ✅ Immediate auth check BEFORE loading any resources -->
    <script>
        (function() {
            // Check token immediately
            if (!getAuthToken()) {
                window.location.replace('login.html');
            }
        })();
    </script>
    <!-- Then load CSS -->
</head>

<body style="visibility: hidden;">  <!-- ✅ Hidden by default -->
    <!-- Content -->
</body>

<script>
$(document).ready(function() {
    if (!initAuth()) return;
    document.body.style.visibility = 'visible'; // ✅ Show after auth
});
</script>
```

## ✅ Router Configuration

### backend/main.py
```python
from auth import routes as auth_routes

# ✅ CORS with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # ✅ Required for auth
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ✅ Include auth routes
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
```

### backend/auth/routes.py
```python
# ✅ No prefix in router (prefix applied in main.py)
router = APIRouter()
```

## 🔍 Common Issues & Solutions

### Issue 1: ModuleNotFoundError: No module named 'auth'
**Solution:** ✅ Fixed - Dockerfile now copies `auth/` directory

### Issue 2: ModuleNotFoundError: No module named 'database'
**Solution:** ✅ Fixed - routes.py now imports `get_db_pool` from `auth.dependencies`

### Issue 3: EmailStr validation error
**Solution:** ✅ Fixed - Added `email-validator==2.1.0` to requirements.txt

### Issue 4: Index.html shows for 1 second before login redirect
**Solution:** ✅ Fixed - Auth check runs immediately in `<head>`, body hidden by default

### Issue 5: bcrypt import error
**Solution:** ✅ Fixed - Added `bcrypt==4.1.2` to requirements.txt

## 🚀 Deployment Command

Run the automated deployment script:
```bash
bash deploy_auth.sh
```

This script will:
1. ✅ Verify all files exist
2. ✅ Stop services
3. ✅ Rebuild backend with auth module
4. ✅ Start services
5. ✅ Wait for PostgreSQL
6. ✅ Run migration
7. ✅ Verify installation

## 🧪 Testing Checklist

After deployment:

- [ ] Backend starts without errors
- [ ] No "ModuleNotFoundError" in logs
- [ ] Navigate to http://localhost:8888
- [ ] Immediately redirects to login.html (no flash)
- [ ] Login with admin/Admin@123 works
- [ ] Redirects to dashboard after login
- [ ] User info shows in navbar
- [ ] Logout works
- [ ] Trying to access index.html without login redirects to login

## 📊 Verification Commands

```bash
# Check backend logs
docker logs ssl-monitor-backend | grep -i error

# Should see:
# ✅ FastAPI application started
# ✅ Successfully connected to PostgreSQL

# Check auth tables
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "\dt"

# Should see:
# ✅ users
# ✅ roles
# ✅ permissions
# ✅ role_permissions
# ✅ sessions
# ✅ audit_logs

# Check admin user
docker exec ssl-monitoring-postgres psql -U ssluser -d ssl_monitor -c "SELECT username, email, role_id FROM users WHERE username='admin'"

# Should see:
# username | email                    | role_id
# ---------+--------------------------+---------
# admin    | admin@sslmonitor.local   |       1

# Test login endpoint
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123"}'

# Should return:
# {
#   "token": "...",
#   "user": {...},
#   "expires_at": "..."
# }
```

## ✅ All Checks Passed

- [x] All auth module files present
- [x] No incorrect imports
- [x] All dependencies in requirements.txt
- [x] Dockerfile copies auth directory
- [x] Frontend has immediate auth check
- [x] CORS configured for credentials
- [x] Router configuration correct
- [x] Migration script ready
- [x] Deployment script created

**Ready for deployment!** 🚀
