# app/services/log_providers/heroku.py

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.services.log_providers.base import (
    BaseLogProvider, LogProviderConfig, LogResponse, LogProviderError,
    AuthenticationError, RateLimitError, ServiceNotFoundError, LogsUnavailableError
)

class HerokuLogProvider(BaseLogProvider):
    """
    Log provider for Heroku platform.
    
    Fetches logs from Heroku apps using the Heroku API.
    Supports both direct API access and logplex sessions.
    """
    
    def __init__(self):
        super().__init__("Heroku")
        self.api_base_url = "https://api.heroku.com"
        self.max_lines = 1500  # Heroku's default limit
        
    @property
    def platform_type(self) -> str:
        return "heroku"
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Test authentication with Heroku API.
        
        Args:
            credentials: Should contain 'api_key'
            
        Returns:
            bool: True if authentication successful
        """
        api_key = credentials.get("api_key")
        if not api_key:
            raise AuthenticationError("Heroku API key is required", self.platform_type)
        
        try:
            # Test authentication by listing apps
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/vnd.heroku+json; version=3",
                "Content-Type": "application/json"
            }
            
            response = await self.make_http_request(
                method="GET",
                url=f"{self.api_base_url}/apps",
                headers=headers,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            raise AuthenticationError(f"Heroku authentication failed: {str(e)}", self.platform_type)
    
    async def fetch_logs(self, config: LogProviderConfig, lines: int = 50) -> LogResponse:
        """
        Fetch logs from Heroku app.
        
        Uses Heroku's logplex API to get application logs.
        """
        start_time = time.time()
        lines = self.validate_lines_parameter(lines)
        
        # Check rate limit
        if not self.check_rate_limit(config.service_id, limit_per_minute=30):
            raise RateLimitError(
                "Rate limit exceeded for Heroku API (30 requests/minute)",
                self.platform_type,
                retry_after=60
            )
        
        try:
            # Validate configuration
            if not self.validate_config(config.credentials):
                raise LogProviderError("Invalid Heroku configuration", "INVALID_CONFIG", self.platform_type)
            
            api_key = config.credentials["api_key"]
            app_name = config.app_name
            
            # First, verify the app exists
            await self._verify_app_exists(api_key, app_name)
            
            # Get log session URL
            log_session_url = await self._create_log_session(api_key, app_name, lines)
            
            # Fetch logs from the session URL
            logs = await self._fetch_logs_from_session(log_session_url)
            
            # Format logs
            formatted_logs = self.format_logs(logs)
            
            fetch_duration = (time.time() - start_time) * 1000
            
            return self.create_success_response(
                service_id=config.service_id,
                logs=formatted_logs,
                lines_requested=lines,
                fetch_duration_ms=fetch_duration,
                app_name=app_name,
                platform_api="heroku_logplex",
                log_source="heroku_app_logs"
            )
            
        except (AuthenticationError, RateLimitError, ServiceNotFoundError, LogsUnavailableError):
            # Re-raise specific errors
            raise
        except Exception as e:
            # Convert to generic error response
            return self.create_error_response(
                service_id=config.service_id,
                error=LogProviderError(f"Heroku log fetch failed: {str(e)}", "FETCH_FAILED", self.platform_type),
                lines_requested=lines
            )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate Heroku-specific configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            bool: True if valid
        """
        required_fields = ["api_key"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required Heroku config field: {field}")
            if not config[field]:
                raise ValueError(f"Empty Heroku config field: {field}")
        
        # Validate API key format (basic check)
        api_key = config["api_key"]
        if not isinstance(api_key, str) or len(api_key) < 10:
            raise ValueError("Invalid Heroku API key format")
        
        return True
    
    async def _verify_app_exists(self, api_key: str, app_name: str):
        """Verify that the Heroku app exists and is accessible"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.heroku+json; version=3"
        }
        
        try:
            response = await self.make_http_request(
                method="GET",
                url=f"{self.api_base_url}/apps/{app_name}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 404:
                raise ServiceNotFoundError(
                    f"Heroku app '{app_name}' not found or not accessible",
                    self.platform_type
                )
            
            app_data = response.json()
            
            # Check if app is accessible
            if not app_data:
                raise ServiceNotFoundError(
                    f"Heroku app '{app_name}' data not available",
                    self.platform_type
                )
                
        except ServiceNotFoundError:
            raise
        except Exception as e:
            raise LogProviderError(
                f"Failed to verify Heroku app '{app_name}': {str(e)}",
                "APP_VERIFICATION_FAILED",
                self.platform_type
            )
    
    async def _create_log_session(self, api_key: str, app_name: str, lines: int) -> str:
        """
        Create a log session with Heroku and get the logplex URL.
        
        Returns:
            str: Log session URL
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/vnd.heroku+json; version=3",
            "Content-Type": "application/json"
        }
        
        # Request log session
        log_session_data = {
            "lines": lines,
            "source": "app",  # Get app logs (not system logs)
            "tail": False     # Get historical logs, not streaming
        }
        
        try:
            response = await self.make_http_request(
                method="POST",
                url=f"{self.api_base_url}/apps/{app_name}/log-sessions",
                headers=headers,
                json_data=log_session_data,
                timeout=15
            )
            
            session_data = response.json()
            logplex_url = session_data.get("logplex_url")
            
            if not logplex_url:
                raise LogsUnavailableError(
                    f"Heroku did not provide log session URL for app '{app_name}'",
                    self.platform_type
                )
            
            return logplex_url
            
        except LogsUnavailableError:
            raise
        except Exception as e:
            raise LogProviderError(
                f"Failed to create Heroku log session for '{app_name}': {str(e)}",
                "LOG_SESSION_FAILED",
                self.platform_type
            )
    
    async def _fetch_logs_from_session(self, logplex_url: str) -> str:
        """
        Fetch logs from the Heroku logplex session URL.
        
        Args:
            logplex_url: URL to fetch logs from
            
        Returns:
            str: Raw log content
        """
        try:
            # Fetch logs from logplex URL (no auth needed for session URL)
            response = await self.make_http_request(
                method="GET",
                url=logplex_url,
                timeout=30  # Longer timeout for log fetching
            )
            
            log_content = response.text
            
            if not log_content:
                raise LogsUnavailableError(
                    "No logs returned from Heroku logplex session",
                    self.platform_type
                )
            
            return log_content
            
        except LogsUnavailableError:
            raise
        except Exception as e:
            raise LogProviderError(
                f"Failed to fetch logs from Heroku logplex: {str(e)}",
                "LOGPLEX_FETCH_FAILED",
                self.platform_type
            )
    
    def format_logs(self, raw_logs: str) -> List[str]:
        """
        Format Heroku logs into list of log lines.
        
        Heroku logs come in this format:
        2025-08-13T17:45:00.123456+00:00 app[web.1]: Log message here
        """
        if not raw_logs:
            return []
        
        # Split into lines and filter empty lines
        log_lines = [line.strip() for line in raw_logs.split('\n') if line.strip()]
        
        # Heroku logs are already well-formatted, just return them
        return log_lines
    
    # ============= HEROKU-SPECIFIC CAPABILITIES =============
    
    @property
    def supports_real_time(self) -> bool:
        """Heroku supports real-time log streaming"""
        return True
    
    @property
    def supports_filtering(self) -> bool:
        """Heroku supports basic log filtering"""
        return True
    
    @property
    def supports_search(self) -> bool:
        """Heroku doesn't support server-side log search"""
        return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get Heroku-specific capabilities"""
        capabilities = super().get_capabilities()
        capabilities.update({
            "max_lines": self.max_lines,
            "log_retention_days": 7,  # Heroku keeps logs for 7 days
            "streaming_supported": True,
            "app_verification": True,
            "source_filtering": ["app", "heroku"],
            "rate_limit_per_minute": 30
        })
        return capabilities