# app/api/routes/logs.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from app.core.database import get_db
from app.services.log_service import log_service
from app.services.log_providers.registry import log_provider_registry
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    service_id: str

class LogsResponse(BaseModel):
    success: bool
    service_id: str
    platform: str
    logs: List[LogEntry]
    metadata: Dict[str, Any]
    timestamp: str
    error_message: str = None

@router.get("/{service_id}", response_model=LogsResponse)
async def get_service_logs(
    service_id: str, 
    lines: int = Query(50, description="Number of log lines to fetch", ge=1, le=1000),
    use_cache: bool = Query(True, description="Use cached response if available"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get logs from a specific service using platform-agnostic log fetching.
    
    Automatically detects the service's platform and fetches logs using the appropriate provider.
    Falls back to HTTP endpoint if platform logs are not available.
    """
    
    try:
        # Use the universal log service
        log_response = await log_service.get_service_logs(
            service_id=service_id,
            lines=lines,
            use_cache=use_cache
        )
        
        # Convert raw logs to structured format
        formatted_logs = _format_logs_for_response(log_response.logs, service_id)
        
        return LogsResponse(
            success=log_response.success,
            service_id=service_id,
            platform=log_response.platform,
            logs=formatted_logs,
            metadata=log_response.metadata,
            timestamp=log_response.timestamp,
            error_message=log_response.error_message
        )
        
    except Exception as e:
        # Create error response in expected format
        return LogsResponse(
            success=False,
            service_id=service_id,
            platform="error",
            logs=[LogEntry(
                timestamp=datetime.utcnow().isoformat() + "Z",
                level="ERROR",
                message=f"Failed to fetch logs: {str(e)}",
                service_id=service_id
            )],
            metadata={
                "lines_requested": lines,
                "lines_returned": 0,
                "error_code": "FETCH_ERROR"
            },
            timestamp=datetime.utcnow().isoformat() + "Z",
            error_message=str(e)
        )

@router.get("/{service_id}/raw")
async def get_service_logs_raw(
    service_id: str,
    lines: int = Query(50, description="Number of log lines to fetch", ge=1, le=1000),
    use_cache: bool = Query(True, description="Use cached response if available")
):
    """
    Get raw logs from a specific service without formatting.
    
    Returns logs exactly as received from the platform.
    """
    
    log_response = await log_service.get_service_logs(
        service_id=service_id,
        lines=lines,
        use_cache=use_cache
    )
    
    return {
        "service_id": service_id,
        "platform": log_response.platform,
        "success": log_response.success,
        "raw_logs": log_response.logs,
        "metadata": log_response.metadata,
        "timestamp": log_response.timestamp,
        "error_message": log_response.error_message
    }

@router.get("/{service_id}/test")
async def test_service_logs(service_id: str):
    """
    Test log fetching for a service and return detailed diagnostics.
    
    Useful for debugging log configuration issues.
    """
    
    test_result = await log_service.test_service_logs(service_id)
    
    return {
        "service_id": service_id,
        "test_result": test_result,
        "available_platforms": log_provider_registry.list_available_platforms(),
        "platform_capabilities": log_provider_registry.get_all_capabilities()
    }

@router.post("/{service_id}/clear-cache")
async def clear_service_log_cache(service_id: str):
    """
    Clear cached log responses for a specific service.
    """
    
    # Clear the entire cache (simple implementation)
    log_service.clear_cache()
    
    return {
        "message": f"Cache cleared for service '{service_id}'",
        "service_id": service_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/platforms/status")
async def get_platforms_status():
    """
    Get status and capabilities of all available log platforms.
    """
    
    return log_service.get_platform_status()

@router.get("/platforms/list")
async def list_available_platforms():
    """
    List all available log platforms and their capabilities.
    """
    
    platforms = []
    for platform_type in log_provider_registry.list_available_platforms():
        capabilities = log_provider_registry.get_platform_capabilities(platform_type)
        provider_class = log_provider_registry._providers[platform_type]
        
        platforms.append({
            "type": platform_type,
            "provider_class": provider_class.__name__,
            "capabilities": capabilities,
            "description": f"Log provider for {platform_type.title()} platform"
        })
    
    return {
        "total_platforms": len(platforms),
        "platforms": platforms,
        "registry_status": log_provider_registry.get_registry_status()
    }

# ============= UTILITY FUNCTIONS =============

def _format_logs_for_response(raw_logs: List[str] | str, service_id: str) -> List[LogEntry]:
    """
    Format raw logs into structured LogEntry objects.
    
    Attempts to parse timestamp and log level from log lines,
    falls back to defaults if parsing fails.
    """
    
    if isinstance(raw_logs, str):
        # Split string into lines
        log_lines = [line.strip() for line in raw_logs.split('\n') if line.strip()]
    elif isinstance(raw_logs, list):
        log_lines = [str(line).strip() for line in raw_logs if line]
    else:
        log_lines = [str(raw_logs)]
    
    formatted_logs = []
    
    for line in log_lines:
        if not line:
            continue
            
        # Try to parse structured log entry
        parsed_entry = _parse_log_line(line, service_id)
        formatted_logs.append(parsed_entry)
    
    return formatted_logs

def _parse_log_line(log_line: str, service_id: str) -> LogEntry:
    """
    Parse a single log line and extract timestamp, level, and message.
    
    Supports common log formats:
    - ISO timestamp at start: "2025-08-13T17:45:00Z INFO: Message"
    - Level keywords: INFO, WARN, ERROR, DEBUG
    - Plain text: treats entire line as message
    """
    
    import re
    
    # Default values
    timestamp = datetime.utcnow().isoformat() + "Z"
    level = "INFO"
    message = log_line
    
    # Try to extract ISO timestamp
    iso_pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)'
    timestamp_match = re.search(iso_pattern, log_line)
    if timestamp_match:
        timestamp = timestamp_match.group(1)
        if not timestamp.endswith('Z'):
            timestamp += 'Z'
        # Remove timestamp from message
        message = log_line.replace(timestamp_match.group(1), '').strip()
    
    # Try to extract log level
    level_pattern = r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b'
    level_match = re.search(level_pattern, message, re.IGNORECASE)
    if level_match:
        level = level_match.group(1).upper()
        # Normalize WARNING to WARN
        if level == "WARNING":
            level = "WARN"
        # Remove level from message
        message = re.sub(level_pattern + r'[:\s]*', '', message, flags=re.IGNORECASE).strip()
    
    # Clean up message
    if not message:
        message = log_line
    
    return LogEntry(
        timestamp=timestamp,
        level=level,
        message=message,
        service_id=service_id
    )