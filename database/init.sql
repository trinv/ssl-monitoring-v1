-- SSL Monitor Database Initialization Script

-- ============================================
-- Enable Extensions
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- Users Table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user', -- 'user', 'admin'
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_role CHECK (role IN ('user', 'admin')),
    CONSTRAINT chk_email_format CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

-- Create indexes for users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================
-- User Sessions Table
-- ============================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    CONSTRAINT chk_expires_after_created CHECK (expires_at > created_at)
);

-- Create indexes for sessions
CREATE INDEX idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_sessions_is_active ON user_sessions(is_active);

-- ============================================
-- Domains Table
-- ============================================
CREATE TABLE IF NOT EXISTS domains (
    id SERIAL PRIMARY KEY,
    domain_name VARCHAR(253) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    last_scanned TIMESTAMP,
    next_scan TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_domain_format CHECK (domain_name ~ '^([a-zA-Z0-9](-?[a-zA-Z0-9])*\.)+[a-zA-Z]{2,}$')
);

-- Create indexes for domains
CREATE INDEX idx_domains_domain_name ON domains(domain_name);
CREATE INDEX idx_domains_is_active ON domains(is_active);
CREATE INDEX idx_domains_last_scanned ON domains(last_scanned);
CREATE INDEX idx_domains_next_scan ON domains(next_scan);

-- ============================================
-- SSL Certificates Table
-- ============================================
CREATE TABLE IF NOT EXISTS ssl_certificates (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    common_name VARCHAR(255),
    subject_alt_names TEXT, -- JSON array of SANs
    issuer VARCHAR(255),
    serial_number VARCHAR(100),
    issued_date DATE,
    expiry_date DATE NOT NULL,
    is_self_signed BOOLEAN DEFAULT false,
    is_valid BOOLEAN DEFAULT true,
    certificate_pem TEXT,
    fingerprint_sha256 VARCHAR(64),
    key_size INTEGER,
    signature_algorithm VARCHAR(100),
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_dates CHECK (issued_date < expiry_date)
);

-- Create indexes for certificates
CREATE INDEX idx_certs_domain_id ON ssl_certificates(domain_id);
CREATE INDEX idx_certs_expiry_date ON ssl_certificates(expiry_date);
CREATE INDEX idx_certs_is_valid ON ssl_certificates(is_valid);
CREATE INDEX idx_certs_scanned_at ON ssl_certificates(scanned_at);

-- ============================================
-- Scan Results Table
-- ============================================
CREATE TABLE IF NOT EXISTS scan_results (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    scan_type VARCHAR(50) NOT NULL, -- 'ssl', 'http_redirect', 'certificate_chain'
    status VARCHAR(20) NOT NULL, -- 'pending', 'running', 'success', 'failed'
    result_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    
    CONSTRAINT chk_scan_type CHECK (scan_type IN ('ssl', 'http_redirect', 'certificate_chain')),
    CONSTRAINT chk_scan_status CHECK (status IN ('pending', 'running', 'success', 'failed'))
);

-- Create indexes for scan results
CREATE INDEX idx_scan_results_domain_id ON scan_results(domain_id);
CREATE INDEX idx_scan_results_status ON scan_results(status);
CREATE INDEX idx_scan_results_scan_type ON scan_results(scan_type);
CREATE INDEX idx_scan_results_started_at ON scan_results(started_at);

-- ============================================
-- Alerts Table
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL, -- 'cert_expiry', 'cert_revoked', 'weak_encryption'
    severity VARCHAR(20) NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

-- Create indexes for alerts
CREATE INDEX idx_alerts_domain_id ON alerts(domain_id);
CREATE INDEX idx_alerts_alert_type ON alerts(alert_type);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_is_resolved ON alerts(is_resolved);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);

-- ============================================
-- Audit Logs Table
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50), -- 'domain', 'certificate', 'scan', 'alert'
    resource_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit logs
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- ============================================
-- Certificate Expiry Notifications Table
-- ============================================
CREATE TABLE IF NOT EXISTS cert_expiry_notifications (
    id SERIAL PRIMARY KEY,
    certificate_id INTEGER NOT NULL REFERENCES ssl_certificates(id) ON DELETE CASCADE,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    days_until_expiry INTEGER,
    notification_type VARCHAR(50) NOT NULL, -- '30days', '14days', '7days', '1day'
    sent_at TIMESTAMP,
    is_sent BOOLEAN DEFAULT false,
    
    CONSTRAINT chk_notification_type CHECK (notification_type IN ('30days', '14days', '7days', '1day'))
);

-- Create indexes for notifications
CREATE INDEX idx_cert_expiry_domain_id ON cert_expiry_notifications(domain_id);
CREATE INDEX idx_cert_expiry_is_sent ON cert_expiry_notifications(is_sent);

-- ============================================
-- API Usage Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS api_metrics (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms FLOAT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for metrics
CREATE INDEX idx_api_metrics_endpoint ON api_metrics(endpoint);
CREATE INDEX idx_api_metrics_created_at ON api_metrics(created_at);

-- ============================================
-- Create Triggers for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_domains_timestamp
    BEFORE UPDATE ON domains
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- ============================================
-- Create Function to Cleanup Expired Sessions
-- ============================================
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM user_sessions
    WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Create Initial Admin User (CHANGE PASSWORD!)
-- ============================================
-- Password: Admin@123456 (MUST BE CHANGED AFTER FIRST LOGIN!)
INSERT INTO users (username, email, password_hash, role, is_active)
SELECT 'admin', 'admin@mona.namestar.com', 
       '$2b$12$EIxEm4Iq0w.Jd.WrLdRKOZvQfZ6EqvnIVgOCJZCXmr4HxF5rZvCi', -- bcrypt hash of 'Admin@123456'
       'admin', true
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

-- ============================================
-- Verify Schema
-- ============================================
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' ORDER BY table_name;