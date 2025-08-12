from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.service import Service
from app.services.config_service import config_service
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter(prefix="/api/v1/config", tags=["config"])

@router.get("/services")
async def get_services_config():
    """Get services configuration from JSON file"""
    services = await config_service.load_services_config()
    return {"services": services}

@router.post("/sync")
async def sync_config(db: AsyncSession = Depends(get_db)):
    """Sync database services to config file"""
    
    # Get all services from database
    result = await db.execute(select(Service).where(Service.is_active == True))
    services = result.scalars().all()
    
    # Convert to dict format
    services_dict = []
    for service in services:
        services_dict.append({
            "service_id": service.service_id,
            "name": service.name,
            "url": service.url,
            "health_endpoint": service.health_endpoint,
            "logs_endpoint": service.logs_endpoint,
            "check_interval": service.check_interval,
            "log_lines": service.log_lines,
            "timeout": service.timeout,
            "expected_status": service.expected_status
        })
    
    # Save to config file
    await config_service.sync_database_to_config(services_dict)
    
    return {"message": f"Synced {len(services_dict)} services to config file"}

@router.get("/export")
async def export_config(db: AsyncSession = Depends(get_db)):
    """Export current database config as JSON"""
    
    result = await db.execute(select(Service).where(Service.is_active == True))
    services = result.scalars().all()
    
    config_data = {
        "services": [
            {
                "service_id": service.service_id,
                "name": service.name,
                "url": service.url,
                "health_endpoint": service.health_endpoint,
                "logs_endpoint": service.logs_endpoint,
                "check_interval": service.check_interval,
                "log_lines": service.log_lines,
                "timeout": service.timeout,
                "expected_status": service.expected_status
            } for service in services
        ]
    }
    
    return config_data