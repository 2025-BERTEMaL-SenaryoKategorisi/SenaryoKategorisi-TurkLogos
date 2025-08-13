"""
Bill model for customer billing information
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class Bill(BaseModel):
    """Fatura bilgileri tablosu."""
    __tablename__ = "bills"
    
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Bill details
    billing_period_start = Column(DateTime)
    billing_period_end = Column(DateTime)
    due_date = Column(DateTime)
    
    # Amounts
    base_amount = Column(Float)  # Package fee
    usage_charges = Column(Float)  # Extra usage
    taxes = Column(Float)
    discounts = Column(Float, default=0.0)
    total_amount = Column(Float)
    
    # Payment
    payment_status = Column(String(20), default="pending")  # pending, paid, overdue, cancelled
    payment_date = Column(DateTime, nullable=True)
    payment_method = Column(String(50), nullable=True)  # credit_card, bank_transfer, etc.
    
    # Usage details
    data_used_gb = Column(Float, default=0.0)
    voice_used_minutes = Column(Integer, default=0)
    sms_used_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="bills")