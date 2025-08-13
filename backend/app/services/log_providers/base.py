# app/services/log_providers/base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import asyncio
import httpx
import time

class LogResponse(BaseModel):
    """Standardized log response format for all platforms"""
    service_id: str
    platform: str
    success: bool
    logs: List[str] | str
    metadata: Dict[str, Any]
    timestamp: str
    error_message: Optional[str] = None

class PlatformCredentials(BaseModel):
    """Base class for platform-specific credentials"""
    pass

class LogProviderConfig(BaseModel):
    """Configuration for log provider"""
    service_id: str
    platform_type: str
    app_name: str
    credentials: Dict[str, Any]
    parameters: Dict[str, Any] = {}

class LogProviderError(Exception):
    """Base exception for log provider errors"""
    def __init__(self, message: str, error_code: str = "UNKNOWN", platform: str = ""):
        self.message = message
        self.error_code = error_code
        self.platform = platform
        super().__init__(self.message)

class AuthenticationError(LogProviderError):
    """Authentication failed with platform"""
    def __init__(self, message: str, platform: str = ""):
        super().__init__(message, "AUTH_FAILED", platform)

class RateLimitError(LogProviderError):
    """Rate limit exceeded on platform"""
    def __init__(self, message: str, platform: str = "", retry_after: int = None):
        super().__init__(message, "RATE_LIMIT", platform)
        self.retry_after = retry_after

class ServiceNotFoundError(LogProviderError):
    """Service not found on platform"""
    def __init__(self, message: str, platform: str = ""):
        super().__init__(message, "SERVICE_NOT_FOUND", platform)

class LogsUnavailableError(LogProviderError):
    """Logs not available for service"""
    def __init__(self, message: str, platform: str = ""):
        super().__init__(message, "LOGS_UNAVAILABLE", platform)

class BaseLogProvider(ABC):
    """
    Abstract base class for all platform log providers.
    
    All platform-specific providers (Heroku, AWS, Azure, etc.) must inherit from this class
    and implement the required abstract methods.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.default_timeout = 30  # seconds
        self.max_lines = 10000     # maximum lines per request
        self.rate_limit_cache = {}  # simple rate limit tracking
    
    @property
    @abstractmethod
    def platform_type(self) -> str:
        """Return the platform type identifier (e.g., 'heroku', 'aws', 'azure')"""
        pass
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the platform using provided credentials.
        
        Args:
            credentials: Platform-specific authentication data
            
        Returns:
            bool: True if authentication successful
            
        Raises:
            AuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    async def fetch_logs(self, config: LogProviderConfig, lines: int = 50) -> LogResponse:
        """
        Fetch logs from the platform for a specific service.
        
        Args:
            config: Service configuration including credentials and app details
            lines: Number of log lines to fetch
            
        Returns:
            LogResponse: Standardized log response
            
        Raises:
            LogProviderError: For any platform-specific errors
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate platform-specific configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    # ============= COMMON HELPER METHODS =============
    
    def validate_lines_parameter(self, lines: int) -> int:
        """Validate and sanitize the lines parameter"""
        if lines < 1:
            return 1
        if lines > self.max_lines:
            return self.max_lines
        return lines
    
    def check_rate_limit(self, service_id: str, limit_per_minute: int = 10) -> bool:
        """
        Simple rate limiting check.
        
        Args:
            service_id: Service identifier
            limit_per_minute: Maximum requests per minute
            
        Returns:
            bool: True if request is allowed
        """
        now = time.time()
        minute_key = f"{service_id}_{int(now // 60)}"
        
        if minute_key not in self.rate_limit_cache:
            self.rate_limit_cache[minute_key] = 0
        
        # Clean old entries
        old_keys = [k for k in self.rate_limit_cache.keys() 
                   if int(k.split('_')[-1]) < int(now // 60) - 2]
        for key in old_keys:
            del self.rate_limit_cache[key]
        
        if self.rate_limit_cache[minute_key] >= limit_per_minute:
            return False
        
        self.rate_limit_cache[minute_key] += 1
        return True
    
    async def make_http_request(
        self, 
        method: str, 
        url: str, 
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        timeout: int = None
    ) -> httpx.Response:
        """
        Common HTTP request method with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            params: Query parameters
            json_data: JSON request body
            timeout: Request timeout in seconds
            
        Returns:
            httpx.Response: HTTP response
            
        Raises:
            LogProviderError: For HTTP errors
        """
        timeout = timeout or self.default_timeout
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data
                )
                
                # Handle common HTTP errors
                if response.status_code == 401:
                    raise AuthenticationError(
                        f"Authentication failed for {self.platform_name}",
                        self.platform_type
                    )
                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    raise RateLimitError(
                        f"Rate limit exceeded for {self.platform_name}",
                        self.platform_type,
                        int(retry_after) if retry_after else None
                    )
                elif response.status_code == 404:
                    raise ServiceNotFoundError(
                        f"Service not found on {self.platform_name}",
                        self.platform_type
                    )
                elif response.status_code >= 500:
                    raise LogProviderError(
                        f"{self.platform_name} server error: {response.status_code}",
                        "SERVER_ERROR",
                        self.platform_type
                    )
                
                response.raise_for_status()
                return response
                
        except httpx.TimeoutException:
            raise LogProviderError(
                f"Timeout connecting to {self.platform_name}",
                "TIMEOUT",
                self.platform_type
            )
        except httpx.NetworkError as e:
            raise LogProviderError(
                f"Network error connecting to {self.platform_name}: {str(e)}",
                "NETWORK_ERROR",
                self.platform_type
            )
    
    def create_success_response(
        self,
        service_id: str,
        logs: List[str] | str,
        lines_requested: int,
        fetch_duration_ms: float,
        **extra_metadata
    ) -> LogResponse:
        """
        Create a standardized success response.
        
        Args:
            service_id: Service identifier
            logs: Log data (list of lines or raw string)
            lines_requested: Number of lines that were requested
            fetch_duration_ms: Time taken to fetch logs
            **extra_metadata: Additional platform-specific metadata
            
        Returns:
            LogResponse: Standardized response
        """
        lines_returned = len(logs) if isinstance(logs, list) else logs.count('\n')
        
        metadata = {
            "lines_requested": lines_requested,
            "lines_returned": lines_returned,
            "fetch_duration_ms": round(fetch_duration_ms, 2),
            "platform": self.platform_type,
            **extra_metadata
        }
        
        return LogResponse(
            service_id=service_id,
            platform=self.platform_type,
            success=True,
            logs=logs,
            metadata=metadata,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
    
    def create_error_response(
        self,
        service_id: str,
        error: Exception,
        lines_requested: int = 0
    ) -> LogResponse:
        """
        Create a standardized error response.
        
        Args:
            service_id: Service identifier
            error: Exception that occurred
            lines_requested: Number of lines that were requested
            
        Returns:
            LogResponse: Standardized error response
        """
        if isinstance(error, LogProviderError):
            error_message = error.message
            error_code = error.error_code
        else:
            error_message = str(error)
            error_code = "UNKNOWN_ERROR"
        
        metadata = {
            "lines_requested": lines_requested,
            "lines_returned": 0,
            "error_code": error_code,
            "platform": self.platform_type
        }
        
        return LogResponse(
            service_id=service_id,
            platform=self.platform_type,
            success=False,
            logs=[],
            metadata=metadata,
            timestamp=datetime.utcnow().isoformat() + "Z",
            error_message=error_message
        )
    
    def format_logs(self, raw_logs: Any) -> List[str]:
        """
        Format platform-specific log data into standardized list of strings.
        
        Args:
            raw_logs: Platform-specific log data
            
        Returns:
            List[str]: Formatted log lines
        """
        if isinstance(raw_logs, list):
            return [str(line).strip() for line in raw_logs if line]
        elif isinstance(raw_logs, str):
            return [line.strip() for line in raw_logs.split('\n') if line.strip()]
        else:
            return [str(raw_logs)]
    
    # ============= PLATFORM CAPABILITY DETECTION =============
    
    @property
    def supports_real_time(self) -> bool:
        """Whether this platform supports real-time log streaming"""
        return False
    
    @property
    def supports_filtering(self) -> bool:
        """Whether this platform supports log filtering"""
        return False
    
    @property
    def supports_search(self) -> bool:
        """Whether this platform supports log search"""
        return False
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get platform capabilities"""
        return {
            "real_time": self.supports_real_time,
            "filtering": self.supports_filtering,
            "search": self.supports_search,
            "authentication_required": True
        }