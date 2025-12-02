"""
Database connection and session management
"""
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# ============================================
# Database Configuration
# ============================================
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ssl_monitor")
DB_USER = os.getenv("DB_USER", "ssluser")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Validate required environment variables
if not DB_PASSWORD:
    raise ValueError("❌ DB_PASSWORD environment variable is required!")

# ============================================
# Database URL
# ============================================
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ============================================
# Engine Configuration
# ============================================
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_POOL_MAX_OVERFLOW", "10")),
    pool_recycle=3600,
    pool_timeout=30,
    # For production, use NullPool if you have connection pooler like PgBouncer
    # poolclass=NullPool if os.getenv("USE_PGBOUNCER") == "true" else None,
)

# ============================================
# Session Factory
# ============================================
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ============================================
# Database Dependency
# ============================================
async def get_db() -> AsyncSession:
    """
    Get database session for FastAPI dependency injection

    Usage:
        @app.get("/")
        async def route(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================
# Context Manager for Manual Session
# ============================================
@asynccontextmanager
async def get_session():
    """
    Context manager for manual database session management

    Usage:
        async with get_session() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ============================================
# Lifecycle Management
# ============================================
async def init_db():
    """Initialize database connection"""
    try:
        logger.info("🔄 Initializing database connection...")
        async with engine.begin() as conn:
            # Test connection
            await conn.run_sync(lambda c: None)
        logger.info("✅ Database connection established")
        logger.info(f"📊 Pool size: {engine.pool.size()}, Max overflow: {engine.pool._max_overflow}")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise

async def close_db():
    """Close database connection"""
    try:
        logger.info("🔄 Closing database connection...")
        await engine.dispose()
        logger.info("✅ Database connection closed")
    except Exception as e:
        logger.error(f"❌ Database shutdown error: {str(e)}")
