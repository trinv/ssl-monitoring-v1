"""
SSL Monitor Backend API
FastAPI application with authentication, rate limiting, and monitoring
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from datetime import datetime, timezone
import logging
import uuid

from backend.database import init_db, close_db
from backend.routes import auth, domains, scan

# ============================================
# Logging Configuration
# ============================================
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "info").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# Security Configuration
# ============================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://mona.namestar.com").split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS]
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "true").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

logger.info(f"🚀 Starting in {ENVIRONMENT} environment")
logger.info(f"✅ CORS Origins allowed: {CORS_ORIGINS}")

# ============================================
# Rate Limiting
# ============================================
limiter = Limiter(key_func=get_remote_address)

# ============================================
# FastAPI Application
# ============================================
app = FastAPI(
    title="SSL Certificate Monitor API",
    description="Real-time SSL certificate monitoring system with automated scanning",
    version="3.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================
# CORS Middleware
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["X-Total-Count", "X-Page-Number", "X-Request-ID"],
    max_age=3600
)

# ============================================
# Security Headers Middleware
# ============================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"

    # CSP
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "upgrade-insecure-requests;"
    )

    # HSTS in production
    if ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    return response

# ============================================
# Request ID Middleware
# ============================================
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracking"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# ============================================
# Logging Middleware
# ============================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = datetime.now(timezone.utc)

    response = await call_next(request)

    process_time = (datetime.now(timezone.utc) - start_time).total_seconds()

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    return response

# ============================================
# Exception Handlers
# ============================================
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, _exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    logger.warning(f"⚠️ Rate limit exceeded for {request.client.host} on {request.url.path}")

    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": 60
        },
        headers={"Retry-After": "60"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"❌ Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)

    # Don't expose internal errors in production
    error_detail = "Internal server error"
    if ENVIRONMENT != "production":
        error_detail = str(exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": error_detail
        }
    )

# ============================================
# Lifecycle Events
# ============================================
@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    try:
        logger.info("🚀 Starting SSL Monitor Backend...")
        await init_db()
        logger.info("✅ Backend started successfully")
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    try:
        logger.info("🔄 Shutting down SSL Monitor Backend...")
        await close_db()
        logger.info("✅ Backend shutdown complete")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {str(e)}")

# ============================================
# Health Check Endpoints
# ============================================
@app.get("/health")
@limiter.limit("1000/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.0.0",
        "environment": ENVIRONMENT
    }

@app.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}

@app.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe"""
    try:
        # Could add database connectivity check here
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"❌ Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": str(e)}
        )

# ============================================
# Include Routers
# ============================================
app.include_router(auth.router)
app.include_router(domains.router)
app.include_router(scan.router)

# ============================================
# Root Endpoint
# ============================================
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "SSL Monitor API",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs" if ENVIRONMENT != "production" else "disabled",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8080")),
        workers=int(os.getenv("BACKEND_WORKERS", "4")),
        log_level=os.getenv("BACKEND_LOG_LEVEL", "info"),
        reload=ENVIRONMENT != "production"
    )
