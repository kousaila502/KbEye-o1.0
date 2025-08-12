from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from ..core.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(String(255), index=True, nullable=False)
    alert_type = Column(String(50), nullable=False)  # service_down, slow_response, etc.
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="warning")  # info, warning, error, critical
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON, nullable=True)  # additional alert data