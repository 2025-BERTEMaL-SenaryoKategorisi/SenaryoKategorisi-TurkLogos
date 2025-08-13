"""
Package change model for tracking package modifications
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class PackageChange(BaseModel):
    """Paket değişikliği geçmişi."""
    __tablename__ = "package_changes"
    
    id = Column(Integer, primary_key=True, index=True)
    change_id = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Change details
    old_package_id = Column(String(50))
    new_package_id = Column(String(50))
    change_reason = Column(String(100))  # upgrade, downgrade, customer_request
    
    # Pricing
    old_price = Column(Float)
    new_price = Column(Float)
    price_difference = Column(Float)
    
    # Status
    status = Column(String(20), default="pending")  # pending, approved, completed, cancelled
    effective_date = Column(DateTime)
    
    # Processing
    processed_by = Column(String(100))  # agent_name or "automated"
    session_id = Column(String(100), nullable=True)  # For tracking AI agent sessions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="package_changes")
