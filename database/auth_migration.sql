-- ============================================================================
-- SSL Monitor - Authentication & Authorization Migration
-- ============================================================================

-- 1. ROLES TABLE
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default roles
INSERT INTO roles (role_name, description) VALUES
('admin', 'Full access to all features including user management'),
('user', 'Can view and manage domains, trigger scans'),
('viewer', 'Read-only access to domains and scan results')
ON CONFLICT (role_name) DO NOTHING;

-- 2. PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    permission_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default permissions
INSERT INTO permissions (permission_name, description) VALUES
('domains.view', 'View domain list and SSL status'),
('domains.create', 'Add new domains'),
('domains.update', 'Update domain information'),
('domains.delete', 'Delete single domain'),
('domains.bulk_add', 'Bulk add multiple domains'),
('domains.bulk_delete', 'Bulk delete domains'),
('scan.trigger', 'Trigger SSL scans'),
('scan.view', 'View scan results and history'),
('export.csv', 'Export data to CSV'),
('users.view', 'View users list'),
('users.create', 'Create new users'),
('users.update', 'Update user information'),
('users.delete', 'Delete users'),
('settings.view', 'View system settings'),
('settings.manage', 'Manage system settings')
ON CONFLICT (permission_name) DO NOTHING;

-- 3. ROLE_PERMISSIONS TABLE
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Grant all permissions to admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions
ON CONFLICT DO NOTHING;

-- Grant user permissions (all except users.* and settings.manage)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 2, id FROM permissions
WHERE permission_name NOT LIKE 'users.%'
  AND permission_name != 'settings.manage'
ON CONFLICT DO NOTHING;

-- Grant viewer permissions (only view and export)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 3, id FROM permissions
WHERE permission_name IN ('domains.view', 'scan.view', 'export.csv', 'settings.view')
ON CONFLICT DO NOTHING;

-- 4. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role_id INTEGER REFERENCES roles(id) DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_active ON users(is_active);

-- Insert default admin user
-- Username: admin
-- Password: Admin@123 (PLEASE CHANGE AFTER FIRST LOGIN!)
-- Password hash generated with: bcrypt.hashpw(b'Admin@123', bcrypt.gensalt(rounds=12))
INSERT INTO users (username, email, password_hash, full_name, role_id, is_active)
VALUES (
    'admin',
    'admin@sslmonitor.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqgdW9E5SC',
    'System Administrator',
    1,
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- 5. SESSIONS TABLE
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- 6. AUDIT_LOGS TABLE
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_username ON audit_logs(username);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_time ON audit_logs(created_at);
CREATE INDEX idx_audit_success ON audit_logs(success);

-- 7. CLEANUP FUNCTION FOR EXPIRED SESSIONS
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- 8. FUNCTION TO UPDATE updated_at TIMESTAMP
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 9. VIEW FOR USER PERMISSIONS
CREATE OR REPLACE VIEW user_permissions AS
SELECT
    u.id as user_id,
    u.username,
    u.email,
    u.full_name,
    u.is_active,
    r.role_name,
    p.permission_name
FROM users u
JOIN roles r ON u.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id;

-- 10. GRANT PERMISSIONS
GRANT SELECT, INSERT, UPDATE, DELETE ON users TO ssluser;
GRANT SELECT, INSERT, UPDATE, DELETE ON sessions TO ssluser;
GRANT SELECT, INSERT ON audit_logs TO ssluser;
GRANT SELECT ON roles TO ssluser;
GRANT SELECT ON permissions TO ssluser;
GRANT SELECT ON role_permissions TO ssluser;
GRANT SELECT ON user_permissions TO ssluser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ssluser;

-- ============================================================================
-- Migration completed successfully
-- Default admin credentials:
--   Username: admin
--   Password: Admin@123
--
-- IMPORTANT: Change the default password after first login!
-- ============================================================================
