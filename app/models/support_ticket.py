"""
Support ticket model for customer support requests
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class SupportTicket(BaseModel):
    """Teknik destek talepleri."""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Ticket details
    issue_type = Column(String(50))  # connection, billing, hardware, account
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    
    # Content
    title = Column(String(200))
    description = Column(Text)
    resolution = Column(Text, nullable=True)
    
    # Assignment
    assigned_agent = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="support_tickets")
    technician_visits = relationship("TechnicianVisit", back_populates="ticket")

# 5. TEKNİSYEN ZİYARETİ MODELI