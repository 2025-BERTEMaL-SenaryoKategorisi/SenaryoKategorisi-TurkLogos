"""
Technician visit model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class TechnicianVisit(BaseModel):
    """Teknisyen ziyareti modeli."""
    __tablename__ = "technician_visits"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(String(50), unique=True, index=True)
    customer_id = Column(String(50), ForeignKey("users.customer_id"))  # Fixed foreign key
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=True)
    
    # Visit details
    visit_type = Column(String(50))  # installation, repair, maintenance, inspection  
    scheduled_date = Column(DateTime)
    actual_date = Column(DateTime, nullable=True)
    technician_name = Column(String(100), nullable=True)
    technician_phone = Column(String(20), nullable=True)
    
    # Visit status
    status = Column(String(20), default="scheduled")  # scheduled, completed, cancelled, rescheduled
    notes = Column(Text, nullable=True)  # LLM tools'ta notes kullanılıyor
    visit_notes = Column(Text, nullable=True)  # Teknisyen notları
    customer_rating = Column(Integer, nullable=True)  # 1-5 rating
    
    # Resolution
    issue_resolved = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="technician_visits")
    user = relationship("User", back_populates="technician_visits")