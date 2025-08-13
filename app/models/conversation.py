"""
Conversation model for AI agent chat history
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class Conversation(BaseModel):
    """AI Agent konuşma geçmişi."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Message details
    message_type = Column(String(20))  # user, assistant, system
    message_content = Column(Text)
    
    # Context
    scenario_type = Column(String(50))  # package_change, billing, technical_support
    authenticated = Column(Boolean, default=False)
    tools_used = Column(JSON, nullable=True)  # List of tools used
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    iteration_count = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")