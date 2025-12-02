"""
Domain management routes
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional, List
import logging
import re

from backend.database import get_db
from backend.models import Domain, SSLCertificate
from backend.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/domains", tags=["domains"])

# ============================================
# Request/Response Models
# ============================================
class DomainCreate(BaseModel):
    """Domain creation model"""
    domain_name: str = Field(..., min_length=3, max_length=253)
    description: Optional[str] = Field(None, max_length=500)

    @validator('domain_name')
    def validate_domain_name(cls, v):
        """Validate domain name format"""
        # Basic domain name validation
        pattern = r'^([a-zA-Z0-9](-?[a-zA-Z0-9])*\.)+[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid domain name format')
        return v.lower()  # Store lowercase

    class Config:
        json_schema_extra = {
            "example": {
                "domain_name": "example.com",
                "description": "Main production website"
            }
        }

class DomainUpdate(BaseModel):
    """Domain update model"""
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class DomainResponse(BaseModel):
    """Domain response model"""
    id: int
    domain_name: str
    description: Optional[str]
    is_active: bool
    last_scanned: Optional[datetime]
    next_scan: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Certificate info if available
    certificate: Optional[dict] = None

    class Config:
        from_attributes = True

# ============================================
# Routes
# ============================================

@router.get("", response_model=dict)
async def get_domains(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None
):
    """
    Get all domains with pagination and filtering
    """
    try:
        # Build query
        query = select(Domain)
        count_query = select(func.count(Domain.id))

        # Apply filters
        filters = []
        if is_active is not None:
            filters.append(Domain.is_active == is_active)
        if search:
            filters.append(Domain.domain_name.ilike(f"%{search}%"))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get domains with pagination
        query = query.order_by(Domain.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        domains = result.scalars().all()

        # Get certificates for domains
        domain_data = []
        for domain in domains:
            cert_query = select(SSLCertificate).where(
                SSLCertificate.domain_id == domain.id
            ).order_by(SSLCertificate.scanned_at.desc()).limit(1)
            cert_result = await db.execute(cert_query)
            cert = cert_result.scalars().first()

            domain_dict = {
                "id": domain.id,
                "domain_name": domain.domain_name,
                "description": domain.description,
                "is_active": domain.is_active,
                "last_scanned": domain.last_scanned.isoformat() if domain.last_scanned else None,
                "next_scan": domain.next_scan.isoformat() if domain.next_scan else None,
                "created_at": domain.created_at.isoformat(),
                "updated_at": domain.updated_at.isoformat(),
                "certificate": {
                    "expiry_date": cert.expiry_date.isoformat() if cert else None,
                    "is_valid": cert.is_valid if cert else None,
                    "days_until_expiry": (cert.expiry_date - datetime.now(timezone.utc)).days if cert and cert.expiry_date else None,
                } if cert else None
            }
            domain_data.append(domain_dict)

        logger.info(f"✅ Retrieved {len(domains)} domains (total: {total})")

        return {
            "data": domain_data,
            "total": total,
            "skip": skip,
            "limit": limit,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }

    except Exception as e:
        logger.error(f"❌ Get domains error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve domains"
        )

@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(
    request: Request,
    domain: DomainCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Create new domain
    """
    try:
        # Check if domain already exists
        stmt = select(Domain).where(Domain.domain_name == domain.domain_name)
        result = await db.execute(stmt)
        existing = result.scalars().first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Domain '{domain.domain_name}' already exists"
            )

        # Create new domain
        new_domain = Domain(
            domain_name=domain.domain_name,
            description=domain.description,
            created_by=current_user["user_id"],
            is_active=True
        )

        db.add(new_domain)
        await db.flush()  # Get ID without committing
        await db.refresh(new_domain)

        logger.info(f"✅ Domain created: {domain.domain_name} by user {current_user['username']}")

        return new_domain

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Create domain error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create domain"
        )

@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Get domain by ID
    """
    try:
        stmt = select(Domain).where(Domain.id == domain_id)
        result = await db.execute(stmt)
        domain = result.scalars().first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {domain_id} not found"
            )

        # Get latest certificate
        cert_query = select(SSLCertificate).where(
            SSLCertificate.domain_id == domain_id
        ).order_by(SSLCertificate.scanned_at.desc()).limit(1)
        cert_result = await db.execute(cert_query)
        cert = cert_result.scalars().first()

        domain_dict = DomainResponse.model_validate(domain)
        if cert:
            domain_dict.certificate = {
                "common_name": cert.common_name,
                "issuer": cert.issuer,
                "expiry_date": cert.expiry_date.isoformat(),
                "is_valid": cert.is_valid,
                "days_until_expiry": (cert.expiry_date - datetime.now(timezone.utc)).days
            }

        return domain_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get domain error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve domain"
        )

@router.put("/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: int,
    domain_update: DomainUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Update domain
    """
    try:
        stmt = select(Domain).where(Domain.id == domain_id)
        result = await db.execute(stmt)
        domain = result.scalars().first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {domain_id} not found"
            )

        # Update fields
        if domain_update.description is not None:
            domain.description = domain_update.description
        if domain_update.is_active is not None:
            domain.is_active = domain_update.is_active

        await db.flush()
        await db.refresh(domain)

        logger.info(f"✅ Domain updated: {domain.domain_name} by user {current_user['username']}")

        return domain

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update domain error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update domain"
        )

@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(verify_token)
):
    """
    Delete domain (soft delete by setting is_active=False)
    """
    try:
        # Check if user is admin
        if current_user["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can delete domains"
            )

        stmt = select(Domain).where(Domain.id == domain_id)
        result = await db.execute(stmt)
        domain = result.scalars().first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {domain_id} not found"
            )

        # Soft delete
        domain.is_active = False
        await db.flush()

        logger.info(f"✅ Domain deleted: {domain.domain_name} by admin {current_user['username']}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete domain error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete domain"
        )
