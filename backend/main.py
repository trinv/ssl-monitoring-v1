"""
SSL Certificate Monitoring API
PostgreSQL Backend - Bash Scanner
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime
import asyncpg
import csv
import io
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "ssl_monitor")
DB_USER = os.getenv("DB_USER", "ssluser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "SSL@Pass123")

# Database pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    logger.info(f"Starting application...")
    logger.info(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    try:
        db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=5,
            max_size=20
        )
        logger.info(f"✅ Successfully connected to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        raise
    
    yield
    
    logger.info("Shutting down...")
    await db_pool.close()
    logger.info("👋 Database connections closed")

app = FastAPI(
    title="SSL Certificate Monitoring API",
    description="PostgreSQL + Bash Scanner",
    version="2.2.0",
    lifespan=lifespan
)

# Add startup event
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application started")
    logger.info(f"API documentation available at: /docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Models ====================

class DomainCreate(BaseModel):
    domain: str
    notes: Optional[str] = None

class DomainBulkCreate(BaseModel):
    domains: List[str]

class DomainBulkDelete(BaseModel):
    domain_ids: List[int]

class SSLStatus(BaseModel):
    id: int
    domain: str
    ssl_status: str
    ssl_expiry_date: Optional[str]
    days_until_expiry: Optional[int]
    https_status: Optional[str]
    redirect_url: Optional[str]
    scan_time: Optional[datetime]
    status_history: Optional[List[dict]] = None

class DashboardSummary(BaseModel):
    total_domains: int
    ssl_valid_count: int
    expired_soon_count: int
    failed_count: int
    last_scan_time: Optional[datetime]

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "status": "ok",
        "message": "SSL Certificate Monitoring API - PostgreSQL + Bash Scanner",
        "version": "2.2.0",
        "port": 8080,
        "database": f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
    }

@app.get("/api/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary():
    # Refresh materialized view
    await db_pool.execute("REFRESH MATERIALIZED VIEW latest_ssl_status")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM dashboard_summary")
        
        if not row:
            return {
                "total_domains": 0,
                "ssl_valid_count": 0,
                "expired_soon_count": 0,
                "failed_count": 0,
                "last_scan_time": None
            }
        
        return {
            "total_domains": row['total_domains'] or 0,
            "ssl_valid_count": row['ssl_valid_count'] or 0,
            "expired_soon_count": row['expired_soon_count'] or 0,
            "failed_count": row['failed_count'] or 0,
            "last_scan_time": row['last_scan_time']
        }

@app.get("/api/domains", response_model=List[SSLStatus])
async def get_domains(
    ssl_status: Optional[str] = Query(None),
    expired_soon: Optional[bool] = Query(None),
    https_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    # Refresh materialized view
    await db_pool.execute("REFRESH MATERIALIZED VIEW latest_ssl_status")
    
    query = """
        SELECT 
            id, domain, ssl_status, ssl_expiry_date, days_until_expiry,
            https_status, redirect_url, scan_time
        FROM latest_ssl_status
        WHERE 1=1
    """
    params = []
    param_count = 1
    
    if ssl_status:
        query += f" AND ssl_status = ${param_count}"
        params.append(ssl_status)
        param_count += 1
    
    if expired_soon:
        query += " AND days_until_expiry IS NOT NULL AND days_until_expiry < 7"
    
    if https_status:
        query += f" AND https_status = ${param_count}"
        params.append(https_status)
        param_count += 1
    
    if search:
        query += f" AND domain ILIKE ${param_count}"
        params.append(f"%{search}%")
        param_count += 1
    
    query += " ORDER BY domain ASC"
    query += f" LIMIT ${param_count} OFFSET ${param_count + 1}"
    params.extend([limit, offset])
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
        
        results = []
        for row in rows:
            domain_dict = dict(row)
            
            # Get status history (last 5 scans)
            history = await conn.fetch("""
                SELECT scan_time, ssl_status, days_until_expiry, https_status
                FROM ssl_scan_results
                WHERE domain_id = $1
                ORDER BY scan_time DESC
                LIMIT 5
            """, row['id'])
            
            domain_dict['status_history'] = [dict(h) for h in history]
            results.append(domain_dict)
        
        return results

@app.post("/api/domains")
async def create_domain(domain: DomainCreate):
    async with db_pool.acquire() as conn:
        try:
            row = await conn.fetchrow("""
                INSERT INTO domains (domain, notes)
                VALUES ($1, $2)
                RETURNING id, domain, created_at
            """, domain.domain.lower().strip(), domain.notes)
            
            return dict(row)
            
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Domain already exists")

@app.post("/api/domains/bulk")
async def create_domains_bulk(bulk: DomainBulkCreate):
    added = []
    failed = []
    
    async with db_pool.acquire() as conn:
        for domain in bulk.domains:
            try:
                domain_clean = domain.lower().strip()
                if not domain_clean:
                    continue
                
                row = await conn.fetchrow("""
                    INSERT INTO domains (domain) VALUES ($1)
                    RETURNING id, domain
                """, domain_clean)
                
                added.append(dict(row))
                
            except asyncpg.UniqueViolationError:
                failed.append({"domain": domain, "reason": "Already exists"})
            except Exception as e:
                failed.append({"domain": domain, "reason": str(e)})
        
        return {
            "total_added": len(added),
            "total_failed": len(failed),
            "added": added,
            "failed": failed
        }

@app.delete("/api/domains/{domain_id}")
async def delete_domain(domain_id: int):
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM domains WHERE id = $1", domain_id)
        
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Domain not found")
        
        return {"message": "Domain deleted successfully"}

@app.post("/api/domains/bulk-delete")
async def bulk_delete_domains(bulk: DomainBulkDelete):
    if not bulk.domain_ids:
        raise HTTPException(status_code=400, detail="No domain IDs provided")
    
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM domains WHERE id = ANY($1::int[])",
            bulk.domain_ids
        )
        
        count = int(result.split()[-1])
        
        return {"message": f"Deleted {count} domains", "deleted_count": count}

@app.get("/api/export/csv")
async def export_csv(ssl_status: Optional[str] = Query(None)):
    # Refresh materialized view
    await db_pool.execute("REFRESH MATERIALIZED VIEW latest_ssl_status")
    
    query = """
        SELECT domain, ssl_status, ssl_expiry_date, days_until_expiry,
               https_status, redirect_url, scan_time
        FROM latest_ssl_status
        WHERE 1=1
    """
    
    async with db_pool.acquire() as conn:
        if ssl_status:
            rows = await conn.fetch(query + " AND ssl_status = $1", ssl_status)
        else:
            rows = await conn.fetch(query)
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'Domain', 'SSL Status', 'Expiry Date', 'Days Until Expiry',
            'HTTPS Status', 'Redirect URL', 'Last Scan'
        ])
        
        for row in rows:
            writer.writerow([
                row['domain'], 
                row['ssl_status'],
                row['ssl_expiry_date'] or '',
                row['days_until_expiry'] or '',
                row['https_status'] or '',
                row['redirect_url'] or '',
                row['scan_time']
            ])
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=ssl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )

@app.post("/api/scan/trigger")
async def trigger_scan():
    return {"message": "Scan will be triggered on next schedule"}

@app.get("/health")
async def health_check():
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
