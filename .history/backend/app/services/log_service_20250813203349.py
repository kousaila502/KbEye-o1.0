# app/services/log_service.py

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.service import Service
from app.services.log_providers.registry import log_provider_registry, log_provider_factory
from app.services.log_providers.base import (
    LogResponse, LogProviderConfig, LogProviderError, 
    AuthenticationError, RateLimitError, ServiceNotFoundError, LogsUnavailableError
)

class LogService:
    """
    Universal log service that fetches logs from any platform.
    
    Integrates with KbEye's service configuration and uses the platform registry
    to route log requests to the appropriate platform provider.
    """
    
    def __init__(self):
        self.registry = log_provider_registry
        self.factory = log_provider_factory
        self.fallback_enabled = True
        self.cache_duration = 60  # Cache responses for 60 seconds
        self._response_cache = {}
    
    async def get_service_logs(
        self, 
        service_id: str, 
        lines: int = 50,
        use_cache: bool = True
    ) -> LogResponse:
        """
        Get logs for a service using its configured platform.
        
        Args:
            service_id: Service identifier
            lines: Number of log lines to fetch
            use_cache: Whether to use cached responses
            
        Returns:
            LogResponse: Standardized log response
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache:
            cached_response = self._get_cached_response(service_id, lines)
            if cached_response:
                return cached_response
        
        try:
            # Get service configuration from database
            service_config = await self._get_service_config(service_id)
            if not service_config:
                return self._create_service_not_found_response(service_id, lines)
            
            # Check if service has platform configuration
            platform_config = service_config.get("platform")
            if not platform_config:
                return await self._try_fallback_methods(service_config, lines, start_time)
            
            # Validate platform configuration
            platform_type = platform_config.get("type")
            if not platform_type:
                return self._create_error_response(
                    service_id, 
                    "Platform type not specified in service configuration",
                    lines,
                    time.time() - start_time
                )
            
            # Check if platform is supported
            if not self.registry.is_platform_supported(platform_type):
                available_platforms = self.registry.list_available_platforms()
                return self._create_error_response(
                    service_id,
                    f"Platform '{platform_type}' not supported. Available: {', '.join(available_platforms)}",
                    lines,
                    time.time() - start_time
                )
            
            # Create provider configuration
            provider_config = self._create_provider_config(service_config, platform_config)
            
            # Fetch logs from platform
            response = await self.registry.fetch_logs(
                platform_type=platform_type,
                config=provider_config,
                lines=lines
            )
            
            # Cache successful response
            if use_cache and response.success:
                self._cache_response(service_id, lines, response)
            
            return response
            
        except AuthenticationError as e:
            return self._create_error_response(
                service_id,
                f"Authentication failed: {e.message}",
                lines,
                time.time() - start_time,
                error_code="AUTH_FAILED"
            )
        except RateLimitError as e:
            return self._create_error_response(
                service_id,
                f"Rate limit exceeded: {e.message}",
                lines,
                time.time() - start_time,
                error_code="RATE_LIMIT",
                retry_after=e.retry_after
            )
        except ServiceNotFoundError as e:
            return self._create_error_response(
                service_id,
                f"Service not found on platform: {e.message}",
                lines,
                time.time() - start_time,
                error_code="SERVICE_NOT_FOUND"
            )
        except LogsUnavailableError as e:
            # Try fallback methods
            service_config = await self._get_service_config(service_id)
            if service_config and self.fallback_enabled:
                return await self._try_fallback_methods(service_config, lines, start_time)
            
            return self._create_error_response(
                service_id,
                f"Logs unavailable: {e.message}",
                lines,
                time.time() - start_time,
                error_code="LOGS_UNAVAILABLE"
            )
        except LogProviderError as e:
            return self._create_error_response(
                service_id,
                f"Platform error: {e.message}",
                lines,
                time.time() - start_time,
                error_code=e.error_code
            )
        except Exception as e:
            return self._create_error_response(
                service_id,
                f"Unexpected error: {str(e)}",
                lines,
                time.time() - start_time,
                error_code="UNEXPECTED_ERROR"
            )
    
    async def _get_service_config(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service configuration from database and config files"""
        try:
            async with AsyncSessionLocal() as db:
                # Get service from database
                result = await db.execute(
                    select(Service).where(
                        Service.service_id == service_id,
                        Service.is_active == True
                    )
                )
                service = result.scalar_one_or_none()
                
                if not service:
                    return None
                
                # Base configuration from database
                config = {
                    "service_id": service.service_id,
                    "name": service.name,
                    "url": service.url,
                    "health_endpoint": service.health_endpoint,
                    "logs_endpoint": service.logs_endpoint,
                    "timeout": service.timeout
                }
                
                # Try to get platform configuration from config files
                try:
                    from app.services.config_service import config_service
                    individual_config = await config_service.load_service_config(service_id)
                    if individual_config and "platform" in individual_config:
                        config["platform"] = individual_config["platform"]
                except Exception as e:
                    print(f"⚠️ Could not load platform config for {service_id}: {e}")
                
                return config
                
        except Exception as e:
            print(f"❌ Error getting service config for {service_id}: {e}")
            return None
    
    def _create_provider_config(
        self, 
        service_config: Dict[str, Any], 
        platform_config: Dict[str, Any]
    ) -> LogProviderConfig:
        """Create a log provider configuration from service and platform config"""
        return LogProviderConfig(
            service_id=service_config["service_id"],
            platform_type=platform_config["type"],
            app_name=platform_config.get("app_name", service_config["service_id"]),
            credentials=platform_config.get("credentials", {}),
            parameters=platform_config.get("parameters", {})
        )
    
    async def _try_fallback_methods(
        self, 
        service_config: Dict[str, Any], 
        lines: int,
        start_time: float
    ) -> LogResponse:
        """Try fallback methods when platform logs are not available"""
        service_id = service_config["service_id"]
        
        # Fallback 1: Try HTTP logs endpoint
        logs_endpoint = service_config.get("logs_endpoint", "/logs")
        if logs_endpoint and service_config.get("url"):
            try:
                response = await self._fetch_logs_via_http(service_config, lines)
                if response.success:
                    return response
            except Exception as e:
                print(f"⚠️ HTTP fallback failed for {service_id}: {e}")
        
        # Fallback 2: Return helpful message
        return self._create_fallback_response(service_id, lines, time.time() - start_time)
    
    async def _fetch_logs_via_http(
        self, 
        service_config: Dict[str, Any], 
        lines: int
    ) -> LogResponse:
        """Fetch logs via HTTP endpoint (fallback method)"""
        import httpx
        
        service_id = service_config["service_id"]
        base_url = service_config["url"].rstrip("/")
        logs_endpoint = service_config.get("logs_endpoint", "/logs")
        timeout = service_config.get("timeout", 5000) / 1000  # Convert to seconds
        
        logs_url = f"{base_url}{logs_endpoint}"
        params = {"lines": lines}
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(logs_url, params=params)
            response.raise_for_status()
            
            logs_data = response.json()
            
            # Extract logs from response
            if isinstance(logs_data, dict):
                logs = logs_data.get("logs", [])
            elif isinstance(logs_data, list):
                logs = logs_data
            else:
                logs = [str(logs_data)]
            
            return LogResponse(
                service_id=service_id,
                platform="http_endpoint",
                success=True,
                logs=logs,
                metadata={
                    "lines_requested": lines,
                    "lines_returned": len(logs) if isinstance(logs, list) else logs.count('\n'),
                    "source": "http_endpoint",
                    "endpoint": logs_url
                },
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
    
    def _create_service_not_found_response(self, service_id: str, lines: int) -> LogResponse:
        """Create response for service not found"""
        return LogResponse(
            service_id=service_id,
            platform="unknown",
            success=False,
            logs=[],
            metadata={
                "lines_requested": lines,
                "lines_returned": 0,
                "error_code": "SERVICE_NOT_FOUND"
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            error_message=f"Service '{service_id}' not found or inactive"
        )
    
    def _create_fallback_response(
        self, 
        service_id: str, 
        lines: int, 
        duration: float
    ) -> LogResponse:
        """Create helpful fallback response when logs are not available"""
        return LogResponse(
            service_id=service_id,
            platform="fallback",
            success=False,
            logs=[
                f"Logs not available for service '{service_id}'",
                "To enable log fetching, configure platform integration:",
                "",
                "1. Add platform configuration to service config:",
                "   {",
                "     \"platform\": {",
                "       \"type\": \"heroku|aws|azure|gcp\",",
                "       \"app_name\": \"your-app-name\",",
                "       \"credentials\": { ... }",
                "     }",
                "   }",
                "",
                "2. Or implement /logs endpoint in your service",
                "",
                f"Supported platforms: {', '.join(self.registry.list_available_platforms())}"
            ],
            metadata={
                "lines_requested": lines,
                "lines_returned": 0,
                "fetch_duration_ms": round(duration * 1000, 2),
                "error_code": "LOGS_NOT_CONFIGURED",
                "available_platforms": self.registry.list_available_platforms()
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            error_message="Logs not configured for this service"
        )
    
    def _create_error_response(
        self,
        service_id: str,
        error_message: str,
        lines: int,
        duration: float,
        error_code: str = "ERROR",
        retry_after: int = None
    ) -> LogResponse:
        """Create standardized error response"""
        metadata = {
            "lines_requested": lines,
            "lines_returned": 0,
            "fetch_duration_ms": round(duration * 1000, 2),
            "error_code": error_code
        }
        
        if retry_after:
            metadata["retry_after_seconds"] = retry_after
        
        return LogResponse(
            service_id=service_id,
            platform="error",
            success=False,
            logs=[],
            metadata=metadata,
            timestamp=datetime.utcnow().isoformat() + "Z",
            error_message=error_message
        )
    
    # ============= CACHING METHODS =============
    
    def _get_cache_key(self, service_id: str, lines: int) -> str:
        """Generate cache key"""
        return f"{service_id}:{lines}"
    
    def _get_cached_response(self, service_id: str, lines: int) -> Optional[LogResponse]:
        """Get cached response if available and fresh"""
        cache_key = self._get_cache_key(service_id, lines)
        
        if cache_key in self._response_cache:
            cached_data = self._response_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_duration:
                return cached_data["response"]
            else:
                # Remove expired cache entry
                del self._response_cache[cache_key]
        
        return None
    
    def _cache_response(self, service_id: str, lines: int, response: LogResponse):
        """Cache a successful response"""
        cache_key = self._get_cache_key(service_id, lines)
        self._response_cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
        
        # Simple cache cleanup - remove old entries
        current_time = time.time()
        expired_keys = [
            key for key, data in self._response_cache.items()
            if current_time - data["timestamp"] > self.cache_duration * 2
        ]
        for key in expired_keys:
            del self._response_cache[key]
    
    # ============= UTILITY METHODS =============
    
    async def test_service_logs(self, service_id: str) -> Dict[str, Any]:
        """Test log fetching for a service and return detailed results"""
        test_start = time.time()
        
        try:
            # Test with small number of lines
            response = await self.get_service_logs(service_id, lines=5, use_cache=False)
            
            test_duration = time.time() - test_start
            
            return {
                "service_id": service_id,
                "success": response.success,
                "platform": response.platform,
                "error_message": response.error_message,
                "test_duration_ms": round(test_duration * 1000, 2),
                "logs_available": len(response.logs) > 0 if isinstance(response.logs, list) else bool(response.logs),
                "metadata": response.metadata
            }
            
        except Exception as e:
            return {
                "service_id": service_id,
                "success": False,
                "error_message": str(e),
                "test_duration_ms": round((time.time() - test_start) * 1000, 2)
            }
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all available platforms"""
        return {
            "available_platforms": self.registry.list_available_platforms(),
            "platform_capabilities": self.registry.get_all_capabilities(),
            "registry_status": self.registry.get_registry_status(),
            "cache_entries": len(self._response_cache),
            "fallback_enabled": self.fallback_enabled
        }
    
    def clear_cache(self):
        """Clear the response cache"""
        self._response_cache.clear()

# Global log service instance
log_service = LogService()