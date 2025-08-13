from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
from app.core.database import get_db
from app.models.service import Service
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

@router.get("/{service_id}")
async def get_service_logs(service_id: str, lines: int = 50, db: AsyncSession = Depends(get_db)):
    
    # Get service info
    result = await db.execute(select(Service).where(Service.service_id == service_id))
    service = result.scalar_one_or_none()
    
    if not service:
        print(f"❌ Service not found: {service_id}")
        raise HTTPException(status_code=404, detail="Service not found")
    
    print(f"✅ Found service: {service.name} at {service.url}")
    
    try:
        # Fetch logs from service
        async with httpx.AsyncClient(timeout=10.0) as client:
            logs_url = f"{service.url.rstrip('/')}{service.logs_endpoint}"
            params = {"lines": min(lines, service.log_lines)}
            
            print(f"🌐 Requesting logs from: {logs_url}")
            response = await client.get(logs_url, params=params)
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                logs_data = response.json()
                print(f"📄 Logs data received: {logs_data}")
                
                # Transform to expected format
                formatted_logs = []
                for log in logs_data.get("logs", []):
                    formatted_logs.append({
                        "timestamp": log.get("timestamp", datetime.now().isoformat() + "Z"),
                        "level": log.get("level", "INFO"),
                        "message": log.get("message", str(log)),
                        "service_id": service.service_id
                    })
                
                result = {"success": True, "data": formatted_logs}
                print(f"✅ Returning: {result}")
                return result
                
    except httpx.TimeoutException as e:
        print(f"⏰ Timeout exception: {e}")
        # Return graceful fallback instead of 504 error
        return {
            "success": True,
            "data": [
                {
                    "timestamp": datetime.now().isoformat() + "Z",
                    "level": "WARN",
                    "message": f"Logs request timeout for {service.name}",
                    "service_id": service.service_id
                }
            ]
        }
    except Exception as e:
        print(f"❌ Exception caught: {type(e).__name__}: {e}")
        # Graceful fallback - return mock logs instead of 502
        result = {
            "success": True,
            "data": [
                {
                    "timestamp": datetime.now().isoformat() + "Z",
                    "level": "INFO",
                    "message": f"Service {service.name} is monitored but logs endpoint unavailable",
                    "service_id": service.service_id
                },
                {
                    "timestamp": (datetime.now() - timedelta(seconds=30)).isoformat() + "Z",
                    "level": "WARN",
                    "message": f"Implement /logs endpoint in {service.name} for detailed logs",
                    "service_id": service.service_id
                }
            ]
        }
        print(f"🔄 Returning fallback: {result}")
        return result