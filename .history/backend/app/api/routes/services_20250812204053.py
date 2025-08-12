from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ...core.database import get_db
from ...models.service import Service
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/services", tags=["services"])

# Pydantic models for request/response
class ServiceCreate(BaseModel):
    service_id: str
    name: str
    url: str
    health_endpoint: str = "/health"
    logs_endpoint: str = "/logs"
    check_interval: int = 30
    log_lines: int = 50
    timeout: int = 5000
    expected_status: int = 200

class ServiceResponse(BaseModel):
    id: int
    service_id: str
    name: str
    url: str
    health_endpoint: str
    logs_endpoint: str
    check_interval: int
    log_lines: int
    timeout: int
    expected_status: int
    is_active: bool
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[ServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    """Get all services"""
    result = await db.execute(select(Service).where(Service.is_active == True))
    services = result.scalars().all()
    return services

@router.post("/", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new service"""
    
    # Check if service_id already exists
    result = await db.execute(select(Service).where(Service.service_id == service.service_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Service ID already exists")
    
    # Create new service
    db_service = Service(**service.dict())
    db.add(db_service)
    await db.commit()
    await db.refresh(db_service)
    
    return db_service

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific service"""
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return service

@router.delete("/{service_id}")
async def delete_service(service_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a service"""
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Soft delete
    service.is_active = False
    await db.commit()
    
    return {"message": "Service deleted successfully"}