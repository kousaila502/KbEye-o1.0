from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict
from urllib.parse import unquote
from app.core.database import get_db
from app.models.monitoring import ServiceCheck
from app.models.service import Service
from app.services.monitor import monitoring_service
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

class HealthStatus(BaseModel):
    service_id: str
    service_name: str
    is_healthy: bool
    status_code: int
    response_time: float
    last_check: datetime
    error_message: str | None = None

class ServiceHealthHistory(BaseModel):
    id: int
    service_id: str
    status_code: int | None
    response_time: float
    is_healthy: bool
    error_message: str | None
    checked_at: datetime

class ForceCheckResponse(BaseModel):
    service_id: str
    service_name: str
    check_result: HealthStatus
    message: str

class HealthSummary(BaseModel):
    total_services: int
    healthy_services: int
    unhealthy_services: int
    average_response_time: float
    last_updated: datetime | None

# ============= GLOBAL MONITORING ENDPOINTS =============

@router.get("/status", response_model=List[HealthStatus])
async def get_services_status(db: AsyncSession = Depends(get_db)):
    """Get current status of all services"""
    
    # Get all services
    services_result = await db.execute(select(Service).where(Service.is_active == True))
    services = services_result.scalars().all()
    
    status_list = []
    for service in services:
        # Get latest check for this service
        check_result = await db.execute(
            select(ServiceCheck)
            .where(ServiceCheck.service_id == service.service_id)
            .order_by(desc(ServiceCheck.checked_at))
            .limit(1)
        )
        latest_check = check_result.scalar_one_or_none()
        
        if latest_check:
            status_list.append(HealthStatus(
                service_id=service.service_id,
                service_name=service.name,
                is_healthy=latest_check.is_healthy,
                status_code=latest_check.status_code or 0,
                response_time=latest_check.response_time,
                last_check=latest_check.checked_at,
                error_message=latest_check.error_message
            ))
    
    return status_list

@router.get("/summary", response_model=HealthSummary)
async def get_health_summary(db: AsyncSession = Depends(get_db)):
    """Get overall health summary of all services"""
    
    # Get all services with their latest checks
    services_result = await db.execute(select(Service).where(Service.is_active == True))
    services = services_result.scalars().all()
    
    healthy_count = 0
    total_response_time = 0.0
    total_services = len(services)
    last_updated = None
    
    for service in services:
        check_result = await db.execute(
            select(ServiceCheck)
            .where(ServiceCheck.service_id == service.service_id)
            .order_by(desc(ServiceCheck.checked_at))
            .limit(1)
        )
        latest_check = check_result.scalar_one_or_none()
        
        if latest_check:
            if latest_check.is_healthy:
                healthy_count += 1
            total_response_time += latest_check.response_time
            
            # Track most recent check time
            if last_updated is None or latest_check.checked_at > last_updated:
                last_updated = latest_check.checked_at
    
    avg_response_time = total_response_time / max(total_services, 1)
    
    return HealthSummary(
        total_services=total_services,
        healthy_services=healthy_count,
        unhealthy_services=total_services - healthy_count,
        average_response_time=avg_response_time,
        last_updated=last_updated
    )

# ============= SINGLE SERVICE MONITORING ENDPOINTS =============

@router.get("/status/{service_id}", response_model=HealthStatus)
async def get_service_health(service_id: str, db: AsyncSession = Depends(get_db)):
    """Get health status for a specific service by ID"""
    
    # Get service
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Get latest check
    check_result = await db.execute(
        select(ServiceCheck)
        .where(ServiceCheck.service_id == service_id)
        .order_by(desc(ServiceCheck.checked_at))
        .limit(1)
    )
    latest_check = check_result.scalar_one_or_none()
    
    if not latest_check:
        raise HTTPException(
            status_code=404, 
            detail=f"No health checks found for service '{service_id}'"
        )
    
    return HealthStatus(
        service_id=service.service_id,
        service_name=service.name,
        is_healthy=latest_check.is_healthy,
        status_code=latest_check.status_code or 0,
        response_time=latest_check.response_time,
        last_check=latest_check.checked_at,
        error_message=latest_check.error_message
    )

@router.get("/status/by-name/{service_name}", response_model=HealthStatus)
async def get_service_health_by_name(service_name: str, db: AsyncSession = Depends(get_db)):
    """Get health status for a specific service by name (URL encoded)"""
    
    # Decode URL-encoded service name
    decoded_name = unquote(service_name)
    
    # Find service by name (case-insensitive)
    service_result = await db.execute(
        select(Service).where(
            Service.name.ilike(f"%{decoded_name}%"),
            Service.is_active == True
        )
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=404, 
            detail=f"Service with name containing '{decoded_name}' not found"
        )
    
    # Use the service_id to get health status
    return await get_service_health(service.service_id, db)

@router.get("/history/{service_id}", response_model=List[ServiceHealthHistory])
async def get_service_health_history(
    service_id: str, 
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get health check history for a specific service"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Get health check history
    history_result = await db.execute(
        select(ServiceCheck)
        .where(ServiceCheck.service_id == service_id)
        .order_by(desc(ServiceCheck.checked_at))
        .limit(limit)
    )
    history = history_result.scalars().all()
    
    return [
        ServiceHealthHistory(
            id=check.id,
            service_id=check.service_id,
            status_code=check.status_code,
            response_time=check.response_time,
            is_healthy=check.is_healthy,
            error_message=check.error_message,
            checked_at=check.checked_at
        )
        for check in history
    ]

@router.get("/check/{service_id}", response_model=ForceCheckResponse)
async def force_health_check(
    service_id: str, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Perform immediate health check for a specific service"""
    
    # Get service
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Perform immediate health check
    try:
        # Use the monitoring service to check this specific service
        check_result = await monitoring_service.check_service_health(service)
        
        # Save the result
        await monitoring_service.save_check_result(check_result)
        
        # Convert to HealthStatus response
        health_status = HealthStatus(
            service_id=service.service_id,
            service_name=service.name,
            is_healthy=check_result['is_healthy'],
            status_code=check_result['status_code'] or 0,
            response_time=check_result['response_time'],
            last_check=datetime.utcnow(),
            error_message=check_result['error_message']
        )
        
        return ForceCheckResponse(
            service_id=service.service_id,
            service_name=service.name,
            check_result=health_status,
            message=f"Immediate health check completed for '{service.name}'"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to perform health check: {str(e)}"
        )

# ============= SERVICE COMPARISON ENDPOINTS =============

@router.get("/compare")
async def compare_services(
    service_ids: str,  # Comma-separated service IDs
    db: AsyncSession = Depends(get_db)
):
    """Compare health status of multiple services"""
    
    service_id_list = [sid.strip() for sid in service_ids.split(",")]
    
    comparison_results = []
    for service_id in service_id_list:
        try:
            health_status = await get_service_health(service_id, db)
            comparison_results.append(health_status)
        except HTTPException:
            # Service not found, add placeholder
            comparison_results.append({
                "service_id": service_id,
                "error": "Service not found"
            })
    
    return {
        "compared_services": len(service_id_list),
        "results": comparison_results
    }

# ============= HEALTH METRICS ENDPOINTS =============

@router.get("/metrics/{service_id}")
async def get_service_metrics(
    service_id: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Get performance metrics for a service over time"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Get checks from last N hours
    from datetime import timedelta
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    metrics_result = await db.execute(
        select(ServiceCheck)
        .where(
            ServiceCheck.service_id == service_id,
            ServiceCheck.checked_at >= cutoff_time
        )
        .order_by(ServiceCheck.checked_at)
    )
    checks = metrics_result.scalars().all()
    
    if not checks:
        return {
            "service_id": service_id,
            "service_name": service.name,
            "period_hours": hours,
            "total_checks": 0,
            "metrics": {}
        }
    
    # Calculate metrics
    total_checks = len(checks)
    healthy_checks = sum(1 for check in checks if check.is_healthy)
    unhealthy_checks = total_checks - healthy_checks
    
    response_times = [check.response_time for check in checks if check.response_time]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    
    uptime_percentage = (healthy_checks / total_checks) * 100 if total_checks > 0 else 0
    
    return {
        "service_id": service_id,
        "service_name": service.name,
        "period_hours": hours,
        "total_checks": total_checks,
        "metrics": {
            "uptime_percentage": round(uptime_percentage, 2),
            "healthy_checks": healthy_checks,
            "unhealthy_checks": unhealthy_checks,
            "avg_response_time": round(avg_response_time, 2),
            "min_response_time": round(min_response_time, 2),
            "max_response_time": round(max_response_time, 2),
            "current_status": checks[-1].is_healthy if checks else None
        }
    }