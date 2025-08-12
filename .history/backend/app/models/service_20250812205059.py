from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base

class Service(Base):
    __tablename__ = "services"
    
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