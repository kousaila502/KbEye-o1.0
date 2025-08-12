from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from ..core.database import Base

class ServiceCheck(Base):
    __tablename__ = "service_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String(255), index=True, nullable=False)
    status_code = Column(Integer)
    response_time = Column(Float)  # milliseconds
    is_healthy = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())

class ServiceLog(Base):
    __tablename__ = "service_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String(255), index=True, nullable=False)
    log_content = Column(Text)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())