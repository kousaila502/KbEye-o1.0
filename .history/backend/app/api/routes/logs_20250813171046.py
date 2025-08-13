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
    """Get logs from a specific service"""
    
    print(f"🔍 Starting logs request for: {service_id}")
    
    try:
        # Get service info
        result = await db.execute(select(Service).where(Service.service_id == service_id))
        service = result.scalar_one_or_none()
        
        if not service:
            print(f"❌ Service not found: {service_id}")
            raise HTTPException(status_code=404, detail="Service not found")
        
        print(f"✅ Found service: {service.name}")
        
        try:
            # Fetch logs from service
            async with httpx.AsyncClient(timeout=10.0) as client:
                logs_url = f"{service.url.rstrip('/')}{service.logs_endpoint}"
                print(f"🌐 Requesting: {logs_url}")
                
                response = await client.get(logs_url, params={"lines": min(lines, service.log_lines)})
                print(f"📡 Response status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ 200 response - processing logs")
                    logs_data = response.json()
                    formatted_logs = []
                    for log in logs_data.get("logs", []):
                        formatted_logs.append({
                            "timestamp": log.get("timestamp", datetime.now().isoformat() + "Z"),
                            "level": log.get("level", "INFO"),
                            "message": log.get("message", str(log)),
                            "service_id": service.service_id
                        })
                    
                    result = {"success": True, "data": formatted_logs}
                    print(f"🎯 Returning 200 result: {result}")
                    return result
                else:
                    print(f"⚠️ Non-200 response: {response.status_code}")
                    result = {
                        "success": True,
                        "data": [
                            {
                                "timestamp": datetime.now().isoformat() + "Z",
                                "level": "ERROR",
                                "message": f"Service returned {response.status_code}",
                                "service_id": service.service_id
                            }
                        ]
                    }
                    print(f"🎯 Returning error result: {result}")
                    return result
                    
        except httpx.TimeoutException as e:
            print(f"⏰ Timeout exception: {e}")
            result = {
                "success": True,
                "data": [
                    {
                        "timestamp": datetime.now().isoformat() + "Z",
                        "level": "WARN",
                        "message": f"Timeout for {service.name}",
                        "service_id": service.service_id
                    }
                ]
            }
            print(f"🎯 Returning timeout result: {result}")
            return result
            
        except Exception as e:
            print(f"❌ HTTP Exception: {type(e).__name__}: {e}")
            result = {
                "success": True,
                "data": [
                    {
                        "timestamp": datetime.now().isoformat() + "Z",
                        "level": "INFO",
                        "message": f"Logs unavailable for {service.name}",
                        "service_id": service.service_id
                    }
                ]
            }
            print(f"🎯 Returning fallback result: {result}")
            return result
            
    except Exception as e:
        print(f"💥 Outer exception: {type(e).__name__}: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }