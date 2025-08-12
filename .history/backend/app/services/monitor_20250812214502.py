import asyncio
import httpx
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.service import Service
from app.models.monitoring import ServiceCheck
from app.api.routes.websocket import manager
from app.services.alert_service import alert_service

class MonitoringService:
    def __init__(self):
        self.is_running = False
        
    async def check_service_health(self, service: Service) -> dict:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=service.timeout/1000) as client:
                health_url = f"{service.url.rstrip('/')}{service.health_endpoint}"
                response = await client.get(health_url)
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                is_healthy = response.status_code == service.expected_status
                
                return {
                    "service_id": service.service_id,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "is_healthy": is_healthy,
                    "error_message": None if is_healthy else f"Expected {service.expected_status}, got {response.status_code}"
                }
                
        except httpx.TimeoutException:
            response_time = service.timeout
            return {
                "service_id": service.service_id,
                "status_code": None,
                "response_time": response_time,
                "is_healthy": False,
                "error_message": f"Timeout after {service.timeout}ms"
            }
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "service_id": service.service_id,
                "status_code": None,
                "response_time": response_time,
                "is_healthy": False,
                "error_message": str(e)
            }
    
    async def save_check_result(self, check_result: dict):
        """Save check result to database"""
        async with AsyncSessionLocal() as db:
            db_check = ServiceCheck(**check_result)
            db.add(db_check)
            await db.commit()
    
    async def monitor_all_services(self):
        """Monitor all active services"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Service).where(Service.is_active == True))
            services = result.scalars().all()
            
            if not services:
                return
            
            # Check all services concurrently
            tasks = [self.check_service_health(service) for service in services]
            results = await asyncio.gather(*tasks)
            
            # Save all results and broadcast updates
            for result in results:
                await self.save_check_result(result)
                print(f"✅ {result['service_id']}: {result['is_healthy']} ({result['response_time']:.1f}ms)")
                
                # Broadcast real-time update
                await manager.broadcast({
                    "type": "health_check",
                    "data": result
                })

    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.is_running = True
        print("🔍 KbEye monitoring started...")
        
        while self.is_running:
            try:
                await self.monitor_all_services()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(5)  # Wait 5 seconds before retrying
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.is_running = False
        print("🛑 KbEye monitoring stopped")

# Global monitoring instance
monitoring_service = MonitoringService()