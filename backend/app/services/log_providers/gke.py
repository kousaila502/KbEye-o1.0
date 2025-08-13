# app/services/log_providers/gke.py

import asyncio
import time
import json
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from app.services.log_providers.base import (
    BaseLogProvider, LogProviderConfig, LogResponse, LogProviderError,
    AuthenticationError, RateLimitError, ServiceNotFoundError, LogsUnavailableError
)

class GKELogProvider(BaseLogProvider):
    """
    Log provider for Google Kubernetes Engine (GKE).
    
    Fetches logs from GKE clusters using Google Cloud Logging API.
    Supports both service account key authentication and workload identity.
    """
    
    def __init__(self):
        super().__init__("Google Kubernetes Engine")
        self.api_base_url = "https://logging.googleapis.com/v2"
        self.oauth_url = "https://oauth2.googleapis.com/token"
        self.max_lines = 1000  # Google Cloud Logging limit
        self.scopes = ["https://www.googleapis.com/auth/logging.read"]
        
    @property
    def platform_type(self) -> str:
        return "gke"
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Test authentication with Google Cloud API.
        
        Args:
            credentials: Should contain service account key or access token
            
        Returns:
            bool: True if authentication successful
        """
        try:
            access_token = await self._get_access_token(credentials)
            
            # Test authentication by listing log entries
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            project_id = credentials.get("project_id")
            if not project_id:
                raise AuthenticationError("GKE project_id is required", self.platform_type)
            
            # Test with a simple log query
            test_body = {
                "resourceNames": [f"projects/{project_id}"],
                "pageSize": 1
            }
            
            response = await self.make_http_request(
                method="POST",
                url=f"{self.api_base_url}/entries:list",
                headers=headers,
                json_data=test_body,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            raise AuthenticationError(f"GKE authentication failed: {str(e)}", self.platform_type)
    
    async def fetch_logs(self, config: LogProviderConfig, lines: int = 50) -> LogResponse:
        """
        Fetch logs from GKE cluster.
        
        Uses Google Cloud Logging API to get container/pod logs.
        """
        start_time = time.time()
        lines = self.validate_lines_parameter(lines)
        
        # Check rate limit
        if not self.check_rate_limit(config.service_id, limit_per_minute=100):
            raise RateLimitError(
                "Rate limit exceeded for Google Cloud Logging API (100 requests/minute)",
                self.platform_type,
                retry_after=60
            )
        
        try:
            # Validate configuration
            if not self.validate_config(config.credentials):
                raise LogProviderError("Invalid GKE configuration", "INVALID_CONFIG", self.platform_type)
            
            # Get access token
            access_token = await self._get_access_token(config.credentials)
            
            project_id = config.credentials["project_id"]
            
            # Build log query based on configuration
            log_filter = self._build_log_filter(config)
            
            # Fetch logs from Google Cloud Logging
            logs = await self._fetch_logs_from_gcp(
                access_token=access_token,
                project_id=project_id,
                log_filter=log_filter,
                lines=lines
            )
            
            # Format logs
            formatted_logs = self.format_logs(logs)
            
            fetch_duration = (time.time() - start_time) * 1000
            
            return self.create_success_response(
                service_id=config.service_id,
                logs=formatted_logs,
                lines_requested=lines,
                fetch_duration_ms=fetch_duration,
                project_id=project_id,
                cluster_name=config.credentials.get("cluster_name", "unknown"),
                platform_api="google_cloud_logging",
                log_source="gke_container_logs"
            )
            
        except (AuthenticationError, RateLimitError, ServiceNotFoundError, LogsUnavailableError):
            # Re-raise specific errors
            raise
        except Exception as e:
            # Convert to generic error response
            return self.create_error_response(
                service_id=config.service_id,
                error=LogProviderError(f"GKE log fetch failed: {str(e)}", "FETCH_FAILED", self.platform_type),
                lines_requested=lines
            )
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate GKE-specific configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            bool: True if valid
        """
        required_fields = ["project_id"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required GKE config field: {field}")
            if not config[field]:
                raise ValueError(f"Empty GKE config field: {field}")
        
        # Validate authentication method
        has_service_account = "service_account_key" in config
        has_access_token = "access_token" in config
        
        if not has_service_account and not has_access_token:
            raise ValueError("GKE requires either 'service_account_key' or 'access_token'")
        
        # Validate service account key format if provided
        if has_service_account:
            service_account_key = config["service_account_key"]
            if isinstance(service_account_key, str):
                try:
                    # Try to parse as JSON
                    json.loads(service_account_key)
                except json.JSONDecodeError:
                    raise ValueError("Invalid service account key format (should be JSON)")
            elif not isinstance(service_account_key, dict):
                raise ValueError("Service account key should be JSON string or dict")
        
        return True
    
    async def _get_access_token(self, credentials: Dict[str, Any]) -> str:
        """Get access token for Google Cloud API"""
        
        # If access token is provided directly, use it
        if "access_token" in credentials:
            return credentials["access_token"]
        
        # Otherwise, use service account key to get access token
        service_account_key = credentials["service_account_key"]
        
        if isinstance(service_account_key, str):
            service_account_data = json.loads(service_account_key)
        else:
            service_account_data = service_account_key
        
        # Create JWT for service account authentication
        jwt_token = await self._create_jwt(service_account_data)
        
        # Exchange JWT for access token
        token_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": jwt_token
        }
        
        response = await self.make_http_request(
            method="POST",
            url=self.oauth_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            params=token_data,
            timeout=10
        )
        
        token_response = response.json()
        access_token = token_response.get("access_token")
        
        if not access_token:
            raise AuthenticationError("Failed to get access token from Google Cloud", self.platform_type)
        
        return access_token
    
    async def _create_jwt(self, service_account_data: Dict[str, Any]) -> str:
        """Create JWT for service account authentication"""
        import jwt
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        
        payload = {
            "iss": service_account_data["client_email"],
            "scope": " ".join(self.scopes),
            "aud": self.oauth_url,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp())
        }
        
        private_key = service_account_data["private_key"]
        
        return jwt.encode(payload, private_key, algorithm="RS256")
    
    def _build_log_filter(self, config: LogProviderConfig) -> str:
        """Build Google Cloud Logging filter query"""
        
        # Base filter for Kubernetes container logs
        base_filter = 'resource.type="k8s_container"'
        
        # Add project filter
        project_id = config.credentials["project_id"]
        
        # Add cluster filter if specified
        cluster_name = config.credentials.get("cluster_name")
        if cluster_name:
            base_filter += f' AND resource.labels.cluster_name="{cluster_name}"'
        
        # Add namespace filter if specified
        namespace = config.credentials.get("namespace", "default")
        base_filter += f' AND resource.labels.namespace_name="{namespace}"'
        
        # Add pod/service filter based on app name
        app_name = config.app_name
        if app_name:
            # Try to match by pod name or labels
            app_filter = f'(resource.labels.pod_name:"{app_name}" OR labels."k8s-pod/app"="{app_name}")'
            base_filter += f' AND {app_filter}'
        
        # Add time filter for recent logs
        time_filter = 'timestamp >= "' + (datetime.utcnow() - timedelta(hours=24)).isoformat() + 'Z"'
        base_filter += f' AND {time_filter}'
        
        return base_filter
    
    async def _fetch_logs_from_gcp(
        self, 
        access_token: str, 
        project_id: str, 
        log_filter: str, 
        lines: int
    ) -> List[Dict[str, Any]]:
        """Fetch logs from Google Cloud Logging API"""
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        request_body = {
            "resourceNames": [f"projects/{project_id}"],
            "filter": log_filter,
            "orderBy": "timestamp desc",
            "pageSize": min(lines, self.max_lines)
        }
        
        try:
            response = await self.make_http_request(
                method="POST",
                url=f"{self.api_base_url}/entries:list",
                headers=headers,
                json_data=request_body,
                timeout=30
            )
            
            response_data = response.json()
            log_entries = response_data.get("entries", [])
            
            if not log_entries:
                raise LogsUnavailableError(
                    f"No logs found for the specified filter in project {project_id}",
                    self.platform_type
                )
            
            return log_entries
            
        except LogsUnavailableError:
            raise
        except Exception as e:
            if "404" in str(e):
                raise ServiceNotFoundError(
                    f"GKE service or project '{project_id}' not found",
                    self.platform_type
                )
            raise LogProviderError(
                f"Failed to fetch logs from Google Cloud: {str(e)}",
                "GCP_API_ERROR",
                self.platform_type
            )
    
    def format_logs(self, raw_logs: List[Dict[str, Any]]) -> List[str]:
        """
        Format Google Cloud log entries into readable log lines.
        
        Google Cloud log entries have this structure:
        {
          "timestamp": "2025-08-13T19:00:00Z",
          "severity": "INFO",
          "textPayload": "Log message",
          "resource": {...},
          "labels": {...}
        }
        """
        if not raw_logs:
            return []
        
        formatted_logs = []
        
        for entry in raw_logs:
            timestamp = entry.get("timestamp", datetime.utcnow().isoformat() + "Z")
            severity = entry.get("severity", "INFO")
            
            # Extract message from different payload types
            message = ""
            if "textPayload" in entry:
                message = entry["textPayload"]
            elif "jsonPayload" in entry:
                json_payload = entry["jsonPayload"]
                message = json_payload.get("message", str(json_payload))
            elif "protoPayload" in entry:
                message = str(entry["protoPayload"])
            else:
                message = str(entry)
            
            # Get pod/container info
            resource = entry.get("resource", {})
            labels = resource.get("labels", {})
            pod_name = labels.get("pod_name", "unknown")
            container_name = labels.get("container_name", "unknown")
            
            # Format log line similar to kubectl logs
            formatted_line = f"{timestamp} {severity} [{pod_name}/{container_name}] {message}"
            formatted_logs.append(formatted_line.strip())
        
        return formatted_logs
    
    # ============= GKE-SPECIFIC CAPABILITIES =============
    
    @property
    def supports_real_time(self) -> bool:
        """GKE supports real-time log streaming via Cloud Logging"""
        return True
    
    @property
    def supports_filtering(self) -> bool:
        """GKE supports advanced log filtering"""
        return True
    
    @property
    def supports_search(self) -> bool:
        """GKE supports server-side log search"""
        return True
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get GKE-specific capabilities"""
        capabilities = super().get_capabilities()
        capabilities.update({
            "max_lines": self.max_lines,
            "log_retention_days": 30,  # Google Cloud default retention
            "streaming_supported": True,
            "cluster_support": True,
            "namespace_filtering": True,
            "pod_filtering": True,
            "severity_filtering": True,
            "timestamp_filtering": True,
            "rate_limit_per_minute": 100,
            "authentication_methods": ["service_account_key", "access_token"]
        })
        return capabilities