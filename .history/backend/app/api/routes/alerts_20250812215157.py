from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from app.core.database import get_db
from app.models.alert import Alert
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
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Get recent alerts"""
    result = await db.execute(
        select(Alert)
        .order_by(desc(Alert.created_at))
        .limit(limit)
    )
    alerts = result.scalars().all()
    return alerts