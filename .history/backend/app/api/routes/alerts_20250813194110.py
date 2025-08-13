from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, update
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.alert import Alert
from app.models.service import Service
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

class AlertResponse(BaseModel):
    id: int
    service_id: str
    alert_type: str
    message: str
    severity: str
    is_resolved: bool
    resolved_at: datetime | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AlertSummaryResponse(BaseModel):
    total_services: int
    services_with_active_alerts: int
    total_active_alerts: int
    total_alerts: int
    alert_breakdown: Dict[str, Dict[str, int]]

class ResolveResponse(BaseModel):
    resolved_count: int
    message: str

# ============= GLOBAL ALERT ENDPOINTS =============

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    limit: int = 50, 
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get recent alerts (all services)"""
    query = select(Alert).order_by(desc(Alert.created_at))
    
    if active_only:
        query = query.where(Alert.is_resolved == False)
    
    query = query.limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    return alerts

@router.get("/summary", response_model=AlertSummaryResponse)
async def get_alert_summary(db: AsyncSession = Depends(get_db)):
    """Get alert summary across all services"""
    
    # Get total services count
    total_services_result = await db.execute(
        select(func.count(Service.service_id)).where(Service.is_active == True)
    )
    total_services = total_services_result.scalar() or 0
    
    # Get total alerts count
    total_alerts_result = await db.execute(select(func.count(Alert.id)))
    total_alerts = total_alerts_result.scalar() or 0
    
    # Get active alerts count
    active_alerts_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.is_resolved == False)
    )
    total_active_alerts = active_alerts_result.scalar() or 0
    
    # Get services with active alerts
    services_with_alerts_result = await db.execute(
        select(func.count(func.distinct(Alert.service_id)))
        .where(Alert.is_resolved == False)
    )
    services_with_active_alerts = services_with_alerts_result.scalar() or 0
    
    # Get alert breakdown by service
    alert_breakdown = {}
    
    # Get all active services
    services_result = await db.execute(
        select(Service.service_id, Service.name).where(Service.is_active == True)
    )
    services = services_result.fetchall()
    
    for service_id, service_name in services:
        # Count active alerts for this service
        active_count_result = await db.execute(
            select(func.count(Alert.id))
            .where(Alert.service_id == service_id, Alert.is_resolved == False)
        )
        active_count = active_count_result.scalar() or 0
        
        # Count total alerts for this service
        total_count_result = await db.execute(
            select(func.count(Alert.id))
            .where(Alert.service_id == service_id)
        )
        total_count = total_count_result.scalar() or 0
        
        alert_breakdown[service_id] = {
            "service_name": service_name,
            "active": active_count,
            "total": total_count
        }
    
    return AlertSummaryResponse(
        total_services=total_services,
        services_with_active_alerts=services_with_active_alerts,
        total_active_alerts=total_active_alerts,
        total_alerts=total_alerts,
        alert_breakdown=alert_breakdown
    )

# ============= SERVICE-SPECIFIC ALERT ENDPOINTS =============

@router.get("/service/{service_id}", response_model=List[AlertResponse])
async def get_service_alerts(
    service_id: str,
    limit: int = 20,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get alerts for a specific service"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Get alerts for this service
    query = select(Alert).where(Alert.service_id == service_id)
    
    if active_only:
        query = query.where(Alert.is_resolved == False)
    
    query = query.order_by(desc(Alert.created_at)).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return alerts

@router.get("/service/{service_id}/active", response_model=List[AlertResponse])
async def get_active_service_alerts(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get only active/unresolved alerts for a specific service"""
    return await get_service_alerts(service_id, limit=50, active_only=True, db=db)

@router.get("/service/{service_id}/count")
async def get_service_alert_count(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get alert counts for a specific service"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Get active count
    active_count_result = await db.execute(
        select(func.count(Alert.id))
        .where(Alert.service_id == service_id, Alert.is_resolved == False)
    )
    active_count = active_count_result.scalar()
    
    # Get total count
    total_count_result = await db.execute(
        select(func.count(Alert.id)).where(Alert.service_id == service_id)
    )
    total_count = total_count_result.scalar()
    
    return {
        "service_id": service_id,
        "service_name": service.name,
        "active_alerts": active_count,
        "total_alerts": total_count
    }

# ============= ALERT MANAGEMENT ENDPOINTS =============

@router.post("/service/{service_id}/resolve-all", response_model=ResolveResponse)
async def resolve_all_service_alerts(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Resolve all active alerts for a specific service"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Update all unresolved alerts for this service
    result = await db.execute(
        update(Alert)
        .where(Alert.service_id == service_id, Alert.is_resolved == False)
        .values(is_resolved=True, resolved_at=datetime.utcnow())
    )
    
    resolved_count = result.rowcount
    await db.commit()
    
    return ResolveResponse(
        resolved_count=resolved_count,
        message=f"Resolved {resolved_count} alerts for service '{service.name}'"
    )

@router.post("/alert/{alert_id}/resolve", response_model=ResolveResponse)
async def resolve_specific_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a specific alert by ID"""
    
    # Find the alert
    alert_result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = alert_result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    
    if alert.is_resolved:
        return ResolveResponse(
            resolved_count=0,
            message=f"Alert {alert_id} was already resolved"
        )
    
    # Resolve the alert
    await db.execute(
        update(Alert)
        .where(Alert.id == alert_id)
        .values(is_resolved=True, resolved_at=datetime.utcnow())
    )
    await db.commit()
    
    return ResolveResponse(
        resolved_count=1,
        message=f"Resolved alert {alert_id} for service '{alert.service_id}'"
    )

@router.delete("/service/{service_id}/cleanup")
async def cleanup_old_service_alerts(
    service_id: str,
    hours_old: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Delete old resolved alerts for a service (cleanup)"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Delete old resolved alerts
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
    
    from sqlalchemy import delete
    result = await db.execute(
        delete(Alert)
        .where(
            Alert.service_id == service_id,
            Alert.is_resolved == True,
            Alert.resolved_at < cutoff_time
        )
    )
    
    deleted_count = result.rowcount
    await db.commit()
    
    return {
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} old alerts for service '{service.name}'"
    }