from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.service import Service
from app.services.config_service import config_service
from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter(prefix="/api/v1/config", tags=["config"])

class ServiceConfigResponse(BaseModel):
    service_id: str
    config_data: Dict
    config_file_path: str
    last_updated: Optional[str] = None

class SyncResponse(BaseModel):
    synced_count: int
    message: str
    details: List[str] = []

class ConfigSummaryResponse(BaseModel):
    config_path: str
    individual_service_configs: int
    service_configs_list: List[str]
    alerts_configs: int
    legacy_files: Dict[str, bool]
    directories: Dict[str, bool]

# ============= LEGACY ENDPOINTS (backward compatibility) =============

@router.get("/services")
async def get_services_config():
    """Get services configuration from legacy JSON file"""
    services = await config_service.load_services_config()
    return {"services": services}

@router.post("/sync")
async def sync_config(db: AsyncSession = Depends(get_db)):
    """Sync database services to legacy config file"""
    
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
    
    # Save to legacy config file
    await config_service.sync_database_to_config(services_dict)
    
    return {"message": f"Synced {len(services_dict)} services to legacy config file"}

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

# ============= INDIVIDUAL SERVICE CONFIG ENDPOINTS =============

@router.get("/service/{service_id}", response_model=ServiceConfigResponse)
async def get_service_config(service_id: str, db: AsyncSession = Depends(get_db)):
    """Get configuration for a specific service"""
    
    # Verify service exists in database
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Load config from individual file
    config_data = await config_service.load_service_config(service_id)
    
    if not config_data:
        # If no individual config exists, create one from database
        config_data = {
            "service_id": service.service_id,
            "name": service.name,
            "url": service.url,
            "health_endpoint": service.health_endpoint,
            "logs_endpoint": service.logs_endpoint,
            "check_interval": service.check_interval,
            "log_lines": service.log_lines,
            "timeout": service.timeout,
            "expected_status": service.expected_status
        }
        await config_service.save_service_config(service_id, config_data)
    
    return ServiceConfigResponse(
        service_id=service_id,
        config_data=config_data,
        config_file_path=f"config/services/{service_id}.json",
        last_updated=config_data.get("updated_at")
    )

@router.post("/service/{service_id}")
async def update_service_config(
    service_id: str, 
    config_data: Dict,
    db: AsyncSession = Depends(get_db)
):
    """Update configuration for a specific service"""
    
    # Verify service exists in database
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Ensure service_id matches
    config_data["service_id"] = service_id
    
    # Save to individual config file
    success = await config_service.save_service_config(service_id, config_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save service config")
    
    return {
        "message": f"Service config updated for '{service_id}'",
        "config_file": f"config/services/{service_id}.json",
        "updated_at": config_data.get("updated_at")
    }

@router.get("/service/{service_id}/alerts")
async def get_service_alerts_config(service_id: str, db: AsyncSession = Depends(get_db)):
    """Get alerts configuration for a specific service"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    alerts_config = await config_service.load_service_alerts_config(service_id)
    
    return {
        "service_id": service_id,
        "alerts_config": alerts_config,
        "config_file": f"config/alerts/{service_id}-alerts.json"
    }

@router.post("/service/{service_id}/alerts")
async def update_service_alerts_config(
    service_id: str,
    alerts_config: Dict,
    db: AsyncSession = Depends(get_db)
):
    """Update alerts configuration for a specific service"""
    
    # Verify service exists
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Ensure service_id matches
    alerts_config["service_id"] = service_id
    
    success = await config_service.save_service_alerts_config(service_id, alerts_config)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save alerts config")
    
    return {
        "message": f"Alerts config updated for '{service_id}'",
        "config_file": f"config/alerts/{service_id}-alerts.json"
    }

# ============= BULK SYNC OPERATIONS =============

@router.post("/sync-all", response_model=SyncResponse)
async def sync_all_services_to_individual_configs(db: AsyncSession = Depends(get_db)):
    """Sync all database services to individual config files"""
    
    # Get all services from database
    result = await db.execute(select(Service).where(Service.is_active == True))
    services = result.scalars().all()
    
    # Convert to dict format
    services_dict = []
    service_names = []
    for service in services:
        service_data = {
            "service_id": service.service_id,
            "name": service.name,
            "url": service.url,
            "health_endpoint": service.health_endpoint,
            "logs_endpoint": service.logs_endpoint,
            "check_interval": service.check_interval,
            "log_lines": service.log_lines,
            "timeout": service.timeout,
            "expected_status": service.expected_status
        }
        services_dict.append(service_data)
        service_names.append(f"{service.service_id} ({service.name})")
    
    # Sync to individual config files
    synced_count = await config_service.sync_database_to_individual_configs(services_dict)
    
    return SyncResponse(
        synced_count=synced_count,
        message=f"Synced {synced_count} services to individual config files",
        details=service_names
    )

@router.post("/service/{service_id}/sync")
async def sync_single_service_config(service_id: str, db: AsyncSession = Depends(get_db)):
    """Sync a single service from database to its individual config file"""
    
    # Get service from database
    service_result = await db.execute(
        select(Service).where(Service.service_id == service_id, Service.is_active == True)
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    
    # Convert to dict format
    service_data = {
        "service_id": service.service_id,
        "name": service.name,
        "url": service.url,
        "health_endpoint": service.health_endpoint,
        "logs_endpoint": service.logs_endpoint,
        "check_interval": service.check_interval,
        "log_lines": service.log_lines,
        "timeout": service.timeout,
        "expected_status": service.expected_status
    }
    
    # Sync to individual config file
    success = await config_service.sync_service_from_database(service_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to sync service config")
    
    return {
        "message": f"Synced service '{service.name}' to config file",
        "service_id": service_id,
        "config_file": f"config/services/{service_id}.json"
    }

# ============= CONFIG MANAGEMENT ENDPOINTS =============

@router.get("/list")
async def list_service_configs():
    """List all services that have individual config files"""
    service_configs = await config_service.list_service_configs()
    
    return {
        "total_configs": len(service_configs),
        "service_configs": service_configs
    }

@router.get("/summary", response_model=ConfigSummaryResponse)
async def get_config_summary():
    """Get summary of all configuration files and directories"""
    summary = await config_service.get_config_summary()
    return ConfigSummaryResponse(**summary)

@router.delete("/service/{service_id}")
async def delete_service_config(service_id: str):
    """Delete individual config files for a service"""
    
    success = await config_service.delete_service_config(service_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete service config")
    
    return {
        "message": f"Deleted config files for service '{service_id}'",
        "deleted_files": [
            f"config/services/{service_id}.json",
            f"config/alerts/{service_id}-alerts.json"
        ]
    }

# ============= TEMPLATE ENDPOINTS =============

@router.post("/create-template")
async def create_service_template():
    """Create service configuration template"""
    await config_service.create_service_template()
    
    return {
        "message": "Service template created",
        "template_file": "config/templates/service-template.json"
    }