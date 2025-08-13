"""
Package model for telecom packages
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class Package(BaseModel):
    """Telecom paketleri tablosu."""
    __tablename__ = "packages"
    
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String(50), unique=True, index=True)  # PN1, PN2, etc.
    name = Column(String(100))  # "MegaPaket 100", "Ekonomik Paket"
    description = Column(Text)
    
    # Pricing
    price = Column(Float)  # Monthly price in TL
    currency = Column(String(10), default="TL")
    
    # Package details
    data_limit_gb = Column(Integer)  # GB limit, -1 for unlimited
    voice_minutes = Column(Integer)  # Voice minutes, -1 for unlimited
    sms_count = Column(Integer)  # SMS count, -1 for unlimited
    internet_speed_mbps = Column(Integer)  # Internet speed
    
    # Features
    features = Column(JSON)  # {"roaming": true, "hotspot": true}
    
    # Status
    is_active = Column(Boolean, default=True)
    is_available_for_new = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="package")
