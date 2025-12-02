"""
Scan management routes
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional
import logging

from backend.database import get_db
from backend.models import Domain, ScanResult
from backend.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scan", tags=["scan"])

# ============================================
# Request/Response Models
# ============================================
class ScanTriggerRequest(BaseModel):
    """Scan trigger request model"""
    domain_id: Optional[int] = None  # None = scan all active domains

class ScanStatusResponse(BaseModel):
    """Scan status response"""
    domain_id: int
    domain_name: str
    status: str
    last_scan: Optional[datetime]
    scan_count: int

# ============================================
# Routes
# ============================================

@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    request: Request,
    scan_request: ScanTriggerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Trigger SSL scan for domain(s)
    Returns 202 Accepted as scan runs in background
    """
    try:
        if scan_request.domain_id:
            # Trigger scan for specific domain
            stmt = select(Domain).where(
                and_(Domain.id == scan_request.domain_id, Domain.is_active == True)
            )
            result = await db.execute(stmt)
            domain = result.scalars().first()

            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Active domain with ID {scan_request.domain_id} not found"
                )

            # Create pending scan result
            scan_result = ScanResult(
                domain_id=domain.id,
                scan_type="ssl",
                status="pending",
                started_at=datetime.now(timezone.utc)
            )
            db.add(scan_result)
            await db.flush()

            logger.info(f"✅ Scan triggered for domain: {domain.domain_name} by {current_user['username']}")

            return {
                "message": f"Scan triggered for domain {domain.domain_name}",
                "domain_id": domain.id,
                "scan_id": scan_result.id
            }
        else:
            # Trigger scan for all active domains
            stmt = select(func.count(Domain.id)).where(Domain.is_active == True)
            from sqlalchemy import func
            result = await db.execute(stmt)
            count = result.scalar()

            logger.info(f"✅ Scan triggered for all {count} active domains by {current_user['username']}")

            return {
                "message": f"Scan triggered for all active domains",
                "domain_count": count
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Trigger scan error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger scan"
        )

@router.get("/status/{domain_id}", response_model=ScanStatusResponse)
async def get_scan_status(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get scan status for domain
    """
    try:
        # Get domain
        domain_stmt = select(Domain).where(Domain.id == domain_id)
        domain_result = await db.execute(domain_stmt)
        domain = domain_result.scalars().first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {domain_id} not found"
            )

        # Get scan count
        from sqlalchemy import func
        count_stmt = select(func.count(ScanResult.id)).where(
            ScanResult.domain_id == domain_id
        )
        count_result = await db.execute(count_stmt)
        scan_count = count_result.scalar()

        # Get latest scan
        latest_stmt = select(ScanResult).where(
            ScanResult.domain_id == domain_id
        ).order_by(ScanResult.started_at.desc()).limit(1)
        latest_result = await db.execute(latest_stmt)
        latest_scan = latest_result.scalars().first()

        return {
            "domain_id": domain.id,
            "domain_name": domain.domain_name,
            "status": latest_scan.status if latest_scan else "never_scanned",
            "last_scan": latest_scan.completed_at if latest_scan else None,
            "scan_count": scan_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get scan status error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scan status"
        )
