-- Simple Authentication Schema
-- Only essential tables for basic login

-- Drop existing tables if any (clean start)
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS roles CASCADE;

-- Roles table (only 2 roles: admin and user)
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(20) UNIQUE NOT NULL,
    description TEXT
);

-- Insert only 2 roles
INSERT INTO roles (id, role_name, description) VALUES
(1, 'admin', 'Administrator - Full access'),
(2, 'user', 'User - Limited access')
ON CONFLICT (role_name) DO NOTHING;

-- Users table (simplified)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role_id INTEGER REFERENCES roles(id) DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster login
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Sessions table (simple token-based)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster session lookup
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- Insert default admin user
-- Password: Admin@123
-- Hash generated with bcrypt cost=12
INSERT INTO users (username, password_hash, full_name, role_id, is_active) VALUES
(
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqgdW9E5SC',
    'System Administrator',
    1,
    TRUE
)
ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ssluser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ssluser;

-- Display created tables
SELECT
    'Users table created' as status,
    COUNT(*) as user_count
FROM users;

SELECT
    'Roles created' as status,
    role_name,
    description
FROM roles
ORDER BY id;
