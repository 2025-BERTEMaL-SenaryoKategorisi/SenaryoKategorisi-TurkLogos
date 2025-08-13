"""
Agent metrics model for tracking AI agent performance
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from .base import BaseModel

class AgentMetrics(BaseModel):
    """AI Agent performans metrikleri."""
    __tablename__ = "agent_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    
    # Performance data
    total_messages = Column(Integer)
    successful_authentications = Column(Integer)
    failed_authentications = Column(Integer)
    tools_called = Column(JSON)  # {"get_user_info": 2, "get_packages": 1}
    
    # Quality metrics
    customer_satisfaction = Column(Float, nullable=True)  # 1-5 rating
    resolution_status = Column(String(20))  # resolved, escalated, incomplete
    
    # Response times
    avg_response_time_ms = Column(Float)
    min_response_time_ms = Column(Integer)
    max_response_time_ms = Column(Integer)
    
    # Session info
    session_duration_minutes = Column(Float)
    conversation_ended_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)