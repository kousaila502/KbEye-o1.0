from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict
from app.core.database import get_db
from app.models.monitoring import ServiceCheck
from app.models.service import Service
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
    error_message: str = None

@router.get("/status", response_model=List[HealthStatus])
async def get_services_status(db: AsyncSession = Depends(get_db)):
    """Get current status of all services"""
    
    # Get latest check for each service
    subquery = select(
        ServiceCheck.service_id,
        desc(ServiceCheck.checked_at).label("latest_check")
    ).group_by(ServiceCheck.service_id).subquery()
    
    # Join with services to get service names
    result = await db.execute(
        select(ServiceCheck, Service.name)
        .join(Service, ServiceCheck.service_id == Service.service_id)
        .join(subquery, 
              (ServiceCheck.service_id == subquery.c.service_id) & 
              (ServiceCheck.checked_at == subquery.c.latest_check))
    )
    
    status_list = []
    for check, service_name in result.all():
        status_list.append(HealthStatus(
            service_id=check.service_id,
            service_name=service_name,
            is_healthy=check.is_healthy,
            status_code=check.status_code or 0,
            response_time=check.response_time,
            last_check=check.checked_at,
            error_message=check.error_message
        ))
    
    return status_list