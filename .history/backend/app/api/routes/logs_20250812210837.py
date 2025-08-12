from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.core.database import get_db
from app.models.service import Service
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

class LogResponse(BaseModel):
    service_id: str
    service_name: str
    logs: List[LogEntry]
    total_lines: int

@router.get("/{service_id}", response_model=LogResponse)
async def get_service_logs(service_id: str, lines: int = 50, db: AsyncSession = Depends(get_db)):
    """Get logs from a specific service"""
    
    # Get service info
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    try:
        # Fetch logs from service
        async with httpx.AsyncClient(timeout=10.0) as client:
            logs_url = f"{service.url.rstrip('/')}{service.logs_endpoint}"
            params = {"lines": min(lines, service.log_lines)}  # Respect service's max lines
            
            response = await client.get(logs_url, params=params)
            
            if response.status_code == 200:
                logs_data = response.json()
                
                return LogResponse(
                    service_id=service.service_id,
                    service_name=service.name,
                    logs=logs_data.get("logs", []),
                    total_lines=len(logs_data.get("logs", []))
                )
            else:
                raise HTTPException(
                    status_code=502, 
                    detail=f"Service returned {response.status_code}: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error fetching logs: {str(e)}")