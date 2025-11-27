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

class SSLStatusHistory(BaseModel):
    ssl_status: str
    scan_time: str  # Format: HH:MM dd/mm/yyyy
    days_until_expiry: Optional[int]

class SSLStatus(BaseModel):
    id: int
    domain: str
    ssl_status: Optional[str]
    ssl_expiry_date: Optional[str]  # Format: dd/mm/yyyy
    days_until_expiry: Optional[int]
    scan_time: Optional[str]  # Format: HH:MM dd/mm/yyyy
    status_history: Optional[List[SSLStatusHistory]] = None

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

class DomainListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    domains: List[SSLStatus]

@app.get("/api/domains", response_model=DomainListResponse)
async def get_domains(
    ssl_status: Optional[str] = Query(None),
    expired_soon: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000)
):
    # Refresh materialized view
    await db_pool.execute("REFRESH MATERIALIZED VIEW latest_ssl_status")

    # Build query
    where_conditions = ["1=1"]
    params = []
    param_count = 1

    if ssl_status:
        where_conditions.append(f"ssl_status = ${param_count}")
        params.append(ssl_status)
        param_count += 1

    if expired_soon:
        where_conditions.append("days_until_expiry IS NOT NULL AND days_until_expiry < 7")

    if search:
        where_conditions.append(f"domain ILIKE ${param_count}")
        params.append(f"%{search}%")
        param_count += 1

    where_clause = " AND ".join(where_conditions)

    async with db_pool.acquire() as conn:
        # Get total count
        total = await conn.fetchval(f"""
            SELECT COUNT(*) FROM latest_ssl_status WHERE {where_clause}
        """, *params)

        total_pages = (total + per_page - 1) // per_page
        offset = (page - 1) * per_page

        # Get paginated data
        query = f"""
            SELECT
                id, domain, ssl_status, ssl_expiry_timestamp, days_until_expiry, scan_time
            FROM latest_ssl_status
            WHERE {where_clause}
            ORDER BY domain ASC
            LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        params.extend([per_page, offset])

        rows = await conn.fetch(query, *params)

        results = []
        for row in rows:
            # Format dates
            expiry_date_str = None
            if row['ssl_expiry_timestamp']:
                expiry_date_str = row['ssl_expiry_timestamp'].strftime('%d/%m/%Y')

            scan_time_str = None
            if row['scan_time']:
                scan_time_str = row['scan_time'].strftime('%H:%M %d/%m/%Y')

            # Get status history (last 5 scans)
            history = await conn.fetch("""
                SELECT scan_time, ssl_status, days_until_expiry
                FROM ssl_scan_results
                WHERE domain_id = $1
                ORDER BY scan_time DESC
                LIMIT 5
            """, row['id'])

            history_list = []
            for h in history:
                history_list.append({
                    'ssl_status': h['ssl_status'],
                    'scan_time': h['scan_time'].strftime('%H:%M %d/%m/%Y') if h['scan_time'] else None,
                    'days_until_expiry': h['days_until_expiry']
                })

            results.append({
                'id': row['id'],
                'domain': row['domain'],
                'ssl_status': row['ssl_status'],
                'ssl_expiry_date': expiry_date_str,
                'days_until_expiry': row['days_until_expiry'],
                'scan_time': scan_time_str,
                'status_history': history_list
            })

        return {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'domains': results
        }

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

class DomainBulkDeleteByName(BaseModel):
    domains: List[str]

@app.post("/api/domains/bulk-delete-by-name")
async def bulk_delete_domains_by_name(bulk: DomainBulkDeleteByName):
    if not bulk.domains:
        raise HTTPException(status_code=400, detail="No domains provided")

    # Normalize domain names (lowercase, trim)
    domain_names = [d.lower().strip() for d in bulk.domains if d.strip()]

    if not domain_names:
        raise HTTPException(status_code=400, detail="No valid domains provided")

    async with db_pool.acquire() as conn:
        # Find matching domains
        rows = await conn.fetch(
            "SELECT id, domain FROM domains WHERE LOWER(domain) = ANY($1::text[])",
            domain_names
        )

        found_domains = [r['domain'] for r in rows]
        domain_ids = [r['id'] for r in rows]
        not_found = [d for d in domain_names if d not in [fd.lower() for fd in found_domains]]

        deleted_count = 0
        if domain_ids:
            result = await conn.execute(
                "DELETE FROM domains WHERE id = ANY($1::int[])",
                domain_ids
            )
            deleted_count = int(result.split()[-1])

        return {
            "deleted_count": deleted_count,
            "found_domains": found_domains,
            "not_found_domains": not_found,
            "message": f"Deleted {deleted_count} domains"
        }

@app.get("/api/export/csv")
async def export_csv(ssl_status: Optional[str] = Query(None)):
    # Refresh materialized view
    await db_pool.execute("REFRESH MATERIALIZED VIEW latest_ssl_status")

    query = """
        SELECT domain, ssl_status, ssl_expiry_timestamp, days_until_expiry, scan_time
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
            'Domain', 'SSL Status', 'Expiry Date', 'Days Until Expiry', 'Last Scan'
        ])

        for row in rows:
            expiry_date = row['ssl_expiry_timestamp'].strftime('%d/%m/%Y') if row['ssl_expiry_timestamp'] else ''
            last_scan = row['scan_time'].strftime('%H:%M %d/%m/%Y') if row['scan_time'] else ''

            writer.writerow([
                row['domain'],
                row['ssl_status'] or '',
                expiry_date,
                row['days_until_expiry'] or '',
                last_scan
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
    """Trigger immediate scan by creating a signal file"""
    try:
        # Create a trigger file that scanner will check
        trigger_file = "/tmp/ssl_scan_trigger"
        with open(trigger_file, 'w') as f:
            f.write(datetime.now().isoformat())

        logger.info("Scan trigger requested - signal file created")
        return {
            "status": "success",
            "message": "Scan triggered successfully. Scanner will start within 10 seconds.",
            "triggered_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering scan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger scan: {str(e)}")

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
