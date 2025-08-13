# app/api/routes/services.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.service import Service
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
    # New platform fields
    platform_type: Optional[str] = None
    platform_app_name: Optional[str] = None
    platform_api_key: Optional[str] = None
    platform_config: Optional[Dict[str, Any]] = None

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
    # New platform fields
    platform_type: Optional[str] = None
    platform_app_name: Optional[str] = None
    platform_api_key: Optional[str] = None
    platform_config: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    health_endpoint: Optional[str] = None
    logs_endpoint: Optional[str] = None
    check_interval: Optional[int] = None
    log_lines: Optional[int] = None
    timeout: Optional[int] = None
    expected_status: Optional[int] = None
    # Platform fields
    platform_type: Optional[str] = None
    platform_app_name: Optional[str] = None
    platform_api_key: Optional[str] = None
    platform_config: Optional[Dict[str, Any]] = None

@router.get("/", response_model=List[ServiceResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    """Get all active services"""
    result = await db.execute(select(Service).where(Service.is_active == True))
    services = result.scalars().all()
    return services

@router.post("/", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new service with platform configuration"""
    
    # Check if service_id already exists
    result = await db.execute(select(Service).where(Service.service_id == service.service_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Service ID already exists")
    
    # Validate platform configuration if provided
    if service.platform_type:
        if not service.platform_app_name:
            # Use service_id as default app name
            service.platform_app_name = service.service_id
        
        if service.platform_type in ["heroku", "aws", "azure", "gcp"] and not service.platform_api_key:
            raise HTTPException(
                status_code=400, 
                detail=f"Platform API key is required for {service.platform_type}"
            )
    
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

@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str, 
    service_update: ServiceUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update a service including platform configuration"""
    
    # Get existing service
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Update fields that are provided
    update_data = service_update.dict(exclude_unset=True)
    
    # Validate platform configuration if being updated
    if "platform_type" in update_data and update_data["platform_type"]:
        platform_type = update_data["platform_type"]
        if platform_type in ["heroku", "aws", "azure", "gcp"]:
            # Check if API key is provided or already exists
            api_key = update_data.get("platform_api_key") or service.platform_api_key
            if not api_key:
                raise HTTPException(
                    status_code=400,
                    detail=f"Platform API key is required for {platform_type}"
                )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(service, field, value)
    
    await db.commit()
    await db.refresh(service)
    
    return service

@router.delete("/{service_id}")
async def delete_service(service_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a service (soft delete)"""
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Soft delete
    service.is_active = False
    await db.commit()
    
    return {"message": "Service deleted successfully"}

@router.post("/{service_id}/test-platform")
async def test_service_platform(service_id: str, db: AsyncSession = Depends(get_db)):
    """Test platform configuration for a service"""
    
    # Get service
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if not service.platform_type:
        raise HTTPException(status_code=400, detail="No platform configuration found")
    
    try:
        # Test platform authentication
        from app.services.log_providers.registry import log_provider_registry
        
        if not log_provider_registry.is_platform_supported(service.platform_type):
            available_platforms = log_provider_registry.list_available_platforms()
            return {
                "success": False,
                "error": f"Platform '{service.platform_type}' not supported",
                "available_platforms": available_platforms
            }
        
        # Test authentication
        credentials = {"api_key": service.platform_api_key}
        auth_success = await log_provider_registry.test_authentication(
            platform_type=service.platform_type,
            credentials=credentials
        )
        
        return {
            "success": auth_success,
            "platform_type": service.platform_type,
            "app_name": service.platform_app_name,
            "message": "Platform authentication successful" if auth_success else "Platform authentication failed"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "platform_type": service.platform_type
        }

@router.get("/{service_id}/platform-status")
async def get_service_platform_status(service_id: str, db: AsyncSession = Depends(get_db)):
    """Get platform status and capabilities for a service"""
    
    # Get service
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if not service.platform_type:
        return {
            "platform_configured": False,
            "message": "No platform configuration found",
            "available_platforms": []
        }
    
    try:
        from app.services.log_providers.registry import log_provider_registry
        
        capabilities = log_provider_registry.get_platform_capabilities(service.platform_type)
        is_supported = log_provider_registry.is_platform_supported(service.platform_type)
        
        return {
            "platform_configured": True,
            "platform_type": service.platform_type,
            "app_name": service.platform_app_name,
            "is_supported": is_supported,
            "capabilities": capabilities,
            "has_api_key": bool(service.platform_api_key)
        }
        
    except Exception as e:
        return {
            "platform_configured": True,
            "platform_type": service.platform_type,
            "error": str(e)
        }