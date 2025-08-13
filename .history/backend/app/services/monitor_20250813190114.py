import asyncio
import httpx
import time
import ssl
from datetime import datetime
from urllib.parse import urlparse
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
        
    def _should_verify_ssl(self, url: str) -> bool:
        """
        Determine if SSL verification should be enabled based on URL.
        Professional approach: verify production domains, skip for development/internal.
        """
        parsed = urlparse(url)
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        
        # Skip SSL verification for development/internal services
        development_patterns = [
            'localhost',
            '127.0.0.1',
            '.nip.io',
            '.xip.io',
            '.ngrok.io',
            '.herokuapp.com',  # Heroku uses proper certs but some apps may have issues
        ]
        
        # Skip for private IP ranges
        private_ips = [
            '192.168.',
            '10.',
            '172.16.', '172.17.', '172.18.', '172.19.',
            '172.20.', '172.21.', '172.22.', '172.23.',
            '172.24.', '172.25.', '172.26.', '172.27.',
            '172.28.', '172.29.', '172.30.', '172.31.'
        ]
        
        # Check development patterns
        for pattern in development_patterns:
            if pattern in hostname:
                return False
                
        # Check private IP ranges
        for ip_range in private_ips:
            if hostname.startswith(ip_range):
                return False
        
        # For production domains, verify SSL
        return True
    
    def _create_ssl_context(self, verify: bool = True):
        """
        Create appropriate SSL context based on verification needs.
        """
        if verify:
            # Use default secure context for production
            return True
        else:
            # Create permissive context for development/internal services
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return ssl_context
    
    async def check_service_health(self, service: Service) -> dict:
        """Check health of a single service with professional SSL handling"""
        start_time = time.time()
        
        try:
            # Determine SSL verification strategy
            should_verify = self._should_verify_ssl(service.url)
            ssl_context = self._create_ssl_context(should_verify)
            
            # Create HTTP client with appropriate SSL settings
            timeout_seconds = service.timeout / 1000
            async with httpx.AsyncClient(
                timeout=timeout_seconds,
                verify=ssl_context,
                follow_redirects=True  # Handle redirects professionally
            ) as client:
                
                health_url = f"{service.url.rstrip('/')}{service.health_endpoint}"
                
                # Add professional headers
                headers = {
                    'User-Agent': 'KbEye-Monitor/1.0',
                    'Accept': 'application/json,text/plain,*/*',
                    'Cache-Control': 'no-cache'
                }
                
                response = await client.get(health_url, headers=headers)
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                is_healthy = response.status_code == service.expected_status
                
                # Enhanced error messaging
                error_message = None
                if not is_healthy:
                    if response.status_code >= 500:
                        error_message = f"Server error: {response.status_code}"
                    elif response.status_code >= 400:
                        error_message = f"Client error: {response.status_code}"
                    else:
                        error_message = f"Expected {service.expected_status}, got {response.status_code}"
                
                return {
                    "service_id": service.service_id,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "is_healthy": is_healthy,
                    "error_message": error_message,
                    "ssl_verified": should_verify
                }
                
        except httpx.TimeoutException:
            response_time = service.timeout
            return {
                "service_id": service.service_id,
                "status_code": 0,
                "response_time": response_time,
                "is_healthy": False,
                "error_message": f"Timeout after {service.timeout}ms",
                "ssl_verified": None
            }
            
        except httpx.ConnectError as e:
            response_time = (time.time() - start_time) * 1000
            error_msg = "Connection failed"
            if "SSL" in str(e):
                error_msg = f"SSL connection failed: {str(e)}"
            elif "DNS" in str(e) or "Name or service not known" in str(e):
                error_msg = f"DNS resolution failed: {str(e)}"
            else:
                error_msg = f"Connection error: {str(e)}"
                
            return {
                "service_id": service.service_id,
                "status_code": 0,
                "response_time": response_time,
                "is_healthy": False,
                "error_message": error_msg,
                "ssl_verified": None
            }
            
        except ssl.SSLError as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "service_id": service.service_id,
                "status_code": 0,
                "response_time": response_time,
                "is_healthy": False,
                "error_message": f"SSL certificate error: {str(e)}",
                "ssl_verified": False
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "service_id": service.service_id,
                "status_code": 0,
                "response_time": response_time,
                "is_healthy": False,
                "error_message": f"Unexpected error: {str(e)}",
                "ssl_verified": None
            }
    
    async def save_check_result(self, check_result: dict):
        """Save check result to database"""
        async with AsyncSessionLocal() as db:
            # Remove ssl_verified from dict before saving (if not in DB schema)
            db_data = {k: v for k, v in check_result.items() if k != 'ssl_verified'}
            db_check = ServiceCheck(**db_data)
            db.add(db_check)
            await db.commit()
    
    async def get_previous_check(self, service_id: str, db: AsyncSession) -> ServiceCheck:
        """Get the previous health check for state comparison"""
        result = await db.execute(
            select(ServiceCheck)
            .where(ServiceCheck.service_id == service_id)
            .order_by(ServiceCheck.checked_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def handle_state_transition(self, service: Service, current_result: dict, previous_check: ServiceCheck):
        """Handle alert logic based on state transitions (healthy ↔ down)"""
        
        # Determine previous state (default to healthy for new services)
        previous_state = previous_check.is_healthy if previous_check else True
        current_state = current_result['is_healthy']
        
        # State transition logic - ONLY alert on state changes
        if previous_state == True and current_state == False:
            # State: healthy → down = CREATE ALERT
            await alert_service.handle_service_down(
                service_id=service.service_id,
                service_name=service.name,
                error_message=current_result.get('error_message', 'Unknown error')
            )
            
        elif previous_state == False and current_state == True:
            # State: down → healthy = RESOLVE ALERTS (auto-resolve, no spam)
            await alert_service.handle_service_recovered(
                service_id=service.service_id,
                service_name=service.name
            )
            
        # else: no state change (healthy→healthy or down→down) = DO NOTHING
        # This prevents alert spam while service stays in same state
    
    async def monitor_all_services(self):
        """Monitor all active services with state-based alerting"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Service).where(Service.is_active == True))
            services = result.scalars().all()
            
            if not services:
                return
            
            # Check all services concurrently
            tasks = [self.check_service_health(service) for service in services]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results with state-based alerting
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Handle task exceptions gracefully
                    service = services[i]
                    result = {
                        "service_id": service.service_id,
                        "status_code": 0,
                        "response_time": 0,
                        "is_healthy": False,
                        "error_message": f"Monitor task failed: {str(result)}",
                        "ssl_verified": None
                    }
                
                service = services[i]
                
                # Get previous check for state comparison BEFORE saving new one
                previous_check = await self.get_previous_check(service.service_id, db)
                
                # Save current check result
                await self.save_check_result(result)
                
                # Handle state-based alerting
                await self.handle_state_transition(service, result, previous_check)
                
                # Enhanced logging with state info
                ssl_info = ""
                if result.get('ssl_verified') is not None:
                    ssl_info = f" [SSL: {'✓' if result['ssl_verified'] else '✗'}]"
                
                # Show state transition in logs
                prev_state = "healthy" if (previous_check.is_healthy if previous_check else True) else "down"
                curr_state = "healthy" if result['is_healthy'] else "down"
                
                if prev_state != curr_state:
                    # State changed - important log
                    status_icon = "🔄"
                    state_info = f" [{prev_state}→{curr_state}]"
                else:
                    # State unchanged - normal log
                    status_icon = "✅" if result['is_healthy'] else "❌"
                    state_info = ""
                
                print(f"{status_icon} {result['service_id']}: {curr_state} "
                      f"({result['response_time']:.1f}ms){ssl_info}{state_info}")
                
                # Broadcast real-time update
                await manager.broadcast({
                    "type": "health_check",
                    "data": result
                })
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.is_running = True
        print("🔍 KbEye monitoring started with state-based alerting...")
        print("📋 Alert logic: healthy→down=ALERT, down→healthy=RESOLVE, no-change=SILENT")
        
        # Run cleanup on startup to resolve very old alerts
        await alert_service.cleanup_old_alerts(hours_old=24)
        
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