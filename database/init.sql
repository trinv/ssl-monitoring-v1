-- SSL Certificate Monitoring System - PostgreSQL Schema
-- Bash Scanner + PostgreSQL (stable combination)

-- ==================== Domains Table ====================
CREATE TABLE IF NOT EXISTS domains (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scanned_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

CREATE INDEX idx_domains_domain ON domains(domain);
CREATE INDEX idx_domains_active ON domains(is_active);

-- ==================== SSL Scan Results Table ====================
CREATE TABLE IF NOT EXISTS ssl_scan_results (
    id SERIAL PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- SSL Status
    ssl_status VARCHAR(20) NOT NULL,
    ssl_expiry_timestamp TIMESTAMP,
    days_until_expiry INTEGER,

    -- Error tracking
    error_message TEXT
);

CREATE INDEX idx_ssl_results_domain_id ON ssl_scan_results(domain_id);
CREATE INDEX idx_ssl_results_scan_time ON ssl_scan_results(scan_time);
CREATE INDEX idx_ssl_results_ssl_status ON ssl_scan_results(ssl_status);
CREATE INDEX idx_ssl_results_days_expiry ON ssl_scan_results(days_until_expiry);

-- ==================== Scan Statistics ====================
CREATE TABLE IF NOT EXISTS scan_stats (
    id SERIAL PRIMARY KEY,
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_domains INTEGER NOT NULL,
    ssl_valid_count INTEGER DEFAULT 0,
    ssl_invalid_count INTEGER DEFAULT 0,
    expired_soon_count INTEGER DEFAULT 0,
    scan_duration_seconds INTEGER
);

CREATE INDEX idx_scan_stats_time ON scan_stats(scan_time);

-- ==================== Materialized View: Latest SSL Status ====================
CREATE MATERIALIZED VIEW IF NOT EXISTS latest_ssl_status AS
SELECT DISTINCT ON (d.id)
    d.id,
    d.domain,
    d.last_scanned_at,
    ssr.ssl_status,
    ssr.ssl_expiry_timestamp,
    ssr.days_until_expiry,
    ssr.scan_time
FROM domains d
LEFT JOIN ssl_scan_results ssr ON d.id = ssr.domain_id
WHERE d.is_active = TRUE
ORDER BY d.id, ssr.scan_time DESC;

CREATE UNIQUE INDEX idx_latest_ssl_status_id ON latest_ssl_status(id);
CREATE INDEX idx_latest_ssl_status_ssl_status ON latest_ssl_status(ssl_status);
CREATE INDEX idx_latest_ssl_status_days_expiry ON latest_ssl_status(days_until_expiry);

-- ==================== View: Dashboard Summary ====================
CREATE OR REPLACE VIEW dashboard_summary AS
SELECT
    COUNT(*) as total_domains,
    COUNT(*) FILTER (WHERE ssl_status = 'VALID') as ssl_valid_count,
    COUNT(*) FILTER (WHERE days_until_expiry IS NOT NULL AND days_until_expiry < 7) as expired_soon_count,
    COUNT(*) FILTER (WHERE ssl_status = 'INVALID') as failed_count,
    MAX(scan_time) as last_scan_time
FROM latest_ssl_status;
