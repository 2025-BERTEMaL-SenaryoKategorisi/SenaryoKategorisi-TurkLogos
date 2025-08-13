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
    
    visit_id = Column(String(50), unique=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Visit details
    scheduled_date = Column(DateTime)
    actual_date = Column(DateTime, nullable=True)
    technician_name = Column(String(100))
    technician_phone = Column(String(20))
    
    # Visit status
    status = Column(String(20), default="scheduled")  # scheduled, completed, cancelled, rescheduled
    visit_notes = Column(Text, nullable=True)
    customer_rating = Column(Integer, nullable=True)  # 1-5 rating
    
    # Resolution
    issue_resolved = Column(Boolean, default=False)
    follow_up_required = Column(Boolean, default=False)
    
    # Relationships
    ticket = relationship("SupportTicket", back_populates="technician_visits")
    user = relationship("User", back_populates="technician_visits")