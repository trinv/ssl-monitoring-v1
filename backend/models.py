"""
SQLAlchemy ORM models for SSL Monitor
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ============================================
# User Model
# ============================================
class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    domains = relationship("Domain", back_populates="created_by_user")
    sessions = relationship("UserSession", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

# ============================================
# User Session Model
# ============================================
class UserSession(Base):
    """User session model"""
    __tablename__ = "user_sessions"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

# ============================================
# Domain Model
# ============================================
class Domain(Base):
    """Domain model"""
    __tablename__ = "domains"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String(253), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    last_scanned = Column(DateTime, nullable=True, index=True)
    next_scan = Column(DateTime, nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by_user = relationship("User", back_populates="domains")
    certificates = relationship("SSLCertificate", back_populates="domain")
    scan_results = relationship("ScanResult", back_populates="domain")
    alerts = relationship("Alert", back_populates="domain")

# ============================================
# SSL Certificate Model
# ============================================
class SSLCertificate(Base):
    """SSL certificate model"""
    __tablename__ = "ssl_certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    common_name = Column(String(255), nullable=True)
    subject_alt_names = Column(Text, nullable=True)
    issuer = Column(String(255), nullable=True)
    serial_number = Column(String(100), nullable=True)
    issued_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=False, index=True)
    is_self_signed = Column(Boolean, default=False)
    is_valid = Column(Boolean, default=True, index=True)
    certificate_pem = Column(Text, nullable=True)
    fingerprint_sha256 = Column(String(64), nullable=True)
    key_size = Column(Integer, nullable=True)
    signature_algorithm = Column(String(100), nullable=True)
    scanned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    domain = relationship("Domain", back_populates="certificates")

# ============================================
# Scan Result Model
# ============================================
class ScanResult(Base):
    """Scan result model"""
    __tablename__ = "scan_results"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    scan_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="scan_results")

# ============================================
# Alert Model
# ============================================
class Alert(Base):
    """Alert model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), default="medium", nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="alerts")

# ============================================
# Audit Log Model
# ============================================
class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")