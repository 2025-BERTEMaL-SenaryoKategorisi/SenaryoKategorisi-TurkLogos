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
    conversation_id = Column(String(100), index=True)  # Session ID olarak kullanılıyor
    user_id = Column(String(50), nullable=True)  # Customer ID string olarak
    
    # Message details - Chat API için
    user_message = Column(Text)  # Kullanıcıdan gelen mesaj
    agent_response = Column(Text)  # Agent'ın verdiği yanıt
    
    # Session context - JSON olarak saklanan bağlam bilgileri
    session_context = Column(JSON, nullable=True)
    
    # Context
    message_type = Column(String(20), default="chat")  # chat, command, system
    scenario_type = Column(String(50), nullable=True)  # package_change, billing, technical_support
    authenticated = Column(Boolean, default=False)
    tools_used = Column(JSON, nullable=True)  # List of tools used in this conversation
    
    # Performance metrics
    processing_time_ms = Column(Integer, nullable=True)
    iteration_count = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - User tablosu ile String ID referansı
    # user = relationship("User", back_populates="conversations")  # Şimdilik kapalı