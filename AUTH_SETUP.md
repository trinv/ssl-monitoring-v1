# Authentication System Setup Guide

## Overview

This guide explains how to set up the authentication system for SSL Certificate Monitoring.

## Components Implemented

### 1. Database Schema
- **Tables Created:**
  - `users` - User accounts with password hashing
  - `roles` - Role definitions (admin, user, viewer)
  - `permissions` - Permission definitions (15 permissions)
  - `role_permissions` - Role-permission mappings
  - `sessions` - Session management with tokens
  - `audit_logs` - Audit trail for all actions

### 2. Backend Authentication (FastAPI)
- **Location:** `backend/auth/`
- **Files:**
  - `models.py` - Pydantic models for authentication
  - `utils.py` - Password hashing, token generation
  - `dependencies.py` - Auth dependencies (get_current_user, require_permission)
  - `routes.py` - Auth endpoints (login, logout, user management)

### 3. Frontend
- **Login Page:** `frontend/login.html` (AdminLTE v2 styled)
- **Auth Logic:** `frontend/js/auth.js`
- **Protected Pages:** `frontend/index.html` (with auth checks)

## Installation Steps

### Quick Install (Recommended)

Run the automated deployment script:

```bash
# Navigate to project directory
cd "d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1"

# Run deployment script
bash rebuild_with_auth.sh
```

This script will:
1. Stop all services
2. Rebuild backend with auth module
3. Start all services
4. Run database migration automatically

### Manual Installation

**Step 1: Rebuild Backend Docker Image**

```bash
cd "d:\VNNIC\4. CA NHAN\Freelancer\Namestar\Monitoring\ssl-monitoring-v1"

# Stop services
docker compose down

# Rebuild backend
docker compose build backend

# Start services
docker compose up -d
```

**Step 2: Run Database Migration**

```bash
# Wait for services to start (about 10 seconds)
sleep 10

# Run migration through Docker
docker exec -i ssl-monitoring-postgres psql -U ssluser -d ssl_monitor < database/auth_migration.sql
```

**Alternative: Using psql directly**

```bash
# Navigate to database directory
cd database

# Run migration script
bash run_auth_migration.sh
```

### Step 3: Verify Installation

1. **Check Tables Created:**
   ```sql
   \dt
   -- Should show: users, roles, permissions, role_permissions, sessions, audit_logs
   ```

2. **Verify Default Admin User:**
   ```sql
   SELECT username, email, full_name FROM users WHERE username = 'admin';
   ```

3. **Check Roles and Permissions:**
   ```sql
   SELECT * FROM roles;
   SELECT COUNT(*) FROM permissions; -- Should return 15
   ```

## Default Accounts

| Username | Password   | Role  | Description           |
|----------|------------|-------|-----------------------|
| admin    | Admin@123  | admin | Full system access    |

## API Endpoints

### Authentication Endpoints

- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/logout` - Logout (requires auth)
- `GET /api/auth/me` - Get current user info (requires auth)
- `POST /api/auth/change-password` - Change password (requires auth)

### Admin-Only Endpoints

- `GET /api/auth/users` - List all users
- `POST /api/auth/users` - Create new user
- `PUT /api/auth/users/{user_id}` - Update user
- `DELETE /api/auth/users/{user_id}` - Delete user
- `GET /api/auth/roles` - List all roles
- `GET /api/auth/permissions` - List all permissions

## Permissions

The system includes 15 granular permissions:

### Domain Management
- `domains.view` - View domains
- `domains.add` - Add new domains
- `domains.edit` - Edit domain information
- `domains.delete` - Delete domains

### SSL Operations
- `ssl.view` - View SSL status
- `ssl.scan` - Trigger SSL scans
- `ssl.export` - Export SSL data

### User Management (Admin only)
- `users.view` - View users
- `users.add` - Add new users
- `users.edit` - Edit user information
- `users.delete` - Delete users

### Role & Permission Management (Admin only)
- `roles.view` - View roles
- `roles.edit` - Edit roles
- `permissions.view` - View permissions
- `permissions.edit` - Edit permissions

## Role Permissions Matrix

| Permission          | Admin | User | Viewer |
|---------------------|-------|------|--------|
| domains.view        | ✓     | ✓    | ✓      |
| domains.add         | ✓     | ✓    | ✗      |
| domains.edit        | ✓     | ✓    | ✗      |
| domains.delete      | ✓     | ✓    | ✗      |
| ssl.view            | ✓     | ✓    | ✓      |
| ssl.scan            | ✓     | ✓    | ✗      |
| ssl.export          | ✓     | ✓    | ✓      |
| users.view          | ✓     | ✗    | ✗      |
| users.add           | ✓     | ✗    | ✗      |
| users.edit          | ✓     | ✗    | ✗      |
| users.delete        | ✓     | ✗    | ✗      |
| roles.view          | ✓     | ✗    | ✗      |
| roles.edit          | ✓     | ✗    | ✗      |
| permissions.view    | ✓     | ✗    | ✗      |
| permissions.edit    | ✓     | ✗    | ✗      |

## Security Features

### Password Security
- Bcrypt hashing with cost factor 12
- Minimum password length: 8 characters
- Password strength validation on change

### Account Protection
- Account locking after 5 failed login attempts
- 30-minute lockout period
- Automatic unlock after lockout expires

### Session Management
- Token-based sessions (32-byte secure random)
- 24-hour session expiry
- Automatic session cleanup
- Session revocation on logout

### Audit Logging
- All authentication events logged
- User management actions tracked
- IP address recording
- Timestamp tracking

## Usage Examples

### Login Flow (Frontend)

```javascript
// Login
const result = await login('admin', 'Admin@123', true);
if (result.success) {
    console.log('Logged in as:', result.user.username);
    // Token stored automatically
}

// Check authentication
if (isAuthenticated()) {
    const user = getCurrentUser();
    console.log('Current user:', user.username);
    console.log('Role:', user.role_name);
    console.log('Permissions:', user.permissions);
}

// Check permissions
if (hasPermission('users.add')) {
    // Show add user button
}

// Logout
await logout(); // Redirects to login page
```

### API Calls with Authentication

```javascript
// Using authFetch (automatic token handling)
const response = await authFetch(`${API_BASE_URL}/domains`, {
    method: 'GET'
});

// Manual token usage
const token = getAuthToken();
const response = await fetch(`${API_BASE_URL}/domains`, {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

## Troubleshooting

### Migration Issues

**Error: "relation already exists"**
- Tables already created. Check if migration was run before.
- To reset: Drop tables and re-run migration

**Error: "password authentication failed"**
- Check database credentials in `.env` or `docker-compose.yml`
- Default: `ssluser` / `SSL@Pass123`

### Login Issues

**Error: "Invalid credentials"**
- Verify username and password (case-sensitive)
- Default admin: `admin` / `Admin@123`

**Error: "Account is locked"**
- Wait 30 minutes or reset via database:
  ```sql
  UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE username = 'admin';
  ```

**Error: "Session expired"**
- Sessions expire after 24 hours
- Clear browser storage and login again

### Backend Issues

**Error: "Module 'auth' not found"**
- Ensure `backend/auth/__init__.py` exists (can be empty)
- Restart backend after adding auth module

**CORS Issues**
- Verify `allow_credentials=True` in `backend/main.py`
- Check browser console for CORS errors

## Next Steps (Optional)

### Add Permission Checks to Existing Endpoints

Update domain endpoints in `backend/main.py`:

```python
from auth.dependencies import get_current_user, require_permission

@app.get("/api/domains")
async def get_domains(
    current_user: User = Depends(require_permission("domains.view")),
    # ... other parameters
):
    # Existing code

@app.post("/api/domains")
async def create_domain(
    domain: DomainCreate,
    current_user: User = Depends(require_permission("domains.add"))
):
    # Existing code
```

### Create User Management UI

Add user management pages to frontend for admin users:
- User list page
- Add/Edit user forms
- Role assignment interface

### Implement Password Reset

Add password reset functionality:
- Forgot password flow
- Email verification
- Reset token generation

## Files Modified

### Database
- ✅ `database/auth_migration.sql` - Authentication schema
- ✅ `database/run_auth_migration.sh` - Migration script

### Backend
- ✅ `backend/main.py` - Added auth routes, updated CORS
- ✅ `backend/auth/__init__.py` - Package initialization (create empty file)
- ✅ `backend/auth/models.py` - Pydantic models
- ✅ `backend/auth/utils.py` - Utility functions
- ✅ `backend/auth/dependencies.py` - FastAPI dependencies
- ✅ `backend/auth/routes.py` - API endpoints

### Frontend
- ✅ `frontend/login.html` - Login page
- ✅ `frontend/js/auth.js` - Authentication logic
- ✅ `frontend/index.html` - Added auth checks, user info display
- ✅ `frontend/js/domains.js` - Updated initialization

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API documentation at `/docs` (FastAPI Swagger UI)
3. Check audit logs for debugging: `SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;`
