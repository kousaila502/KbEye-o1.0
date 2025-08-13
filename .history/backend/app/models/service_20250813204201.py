# app/models/service.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Service(Base):
    __tablename__ = "services"
    
    # Existing fields
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    health_endpoint = Column(String(255), default="/health")
    logs_endpoint = Column(String(255), default="/logs")
    check_interval = Column(Integer, default=30)  # seconds
    log_lines = Column(Integer, default=50)  # number of log lines to fetch
    timeout = Column(Integer, default=5000)  # milliseconds
    expected_status = Column(Integer, default=200)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # New platform fields for log fetching
    platform_type = Column(String(50), nullable=True)        # "heroku", "aws", "azure", "gcp", etc.
    platform_app_name = Column(String(255), nullable=True)   # App/service name on the platform
    platform_api_key = Column(Text, nullable=True)           # API token/key for platform
    platform_config = Column(JSON, nullable=True)            # Additional platform-specific config