"""
User model implementation
"""
from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    """Enhanced User model with full authentication fields."""
    __tablename__ = "users"
    
    # Basic info
    customer_id = Column(String(50), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    
    # 🔐 ENHANCED AUTHENTICATION FIELDS
    tc_kimlik = Column(String(11), unique=True, nullable=False, index=True)  # TC Identity Number
    birth_date = Column(Date, nullable=False)                   # Birth Date for verification
    
    # Security fields
    failed_auth_attempts = Column(Integer, default=0)
    last_auth_attempt = Column(DateTime, nullable=True)
    account_locked_until = Column(DateTime, nullable=True)
    
    # Account info
    account_status = Column(String(20), default="active")  # active, suspended, closed
    customer_type = Column(String(20), default="individual")  # individual, corporate
    current_package_id = Column(String(50), ForeignKey("packages.package_id"))
    contract_end_date = Column(DateTime)
    
    # Financial info
    payment_status = Column(String(20), default="paid")  # paid, pending, overdue
    balance = Column(Float, default=0.0)
    credit_limit = Column(Float, default=1000.0)
    
    # Usage stats
    data_usage_gb = Column(Float, default=0.0)
    voice_usage_minutes = Column(Integer, default=0)
    
    # Address
    address = Column(Text)
    city = Column(String(50))
    region = Column(String(50))
    postal_code = Column(String(10))
    
    # Relationships
    package = relationship("Package", back_populates="users")
    bills = relationship("Bill", back_populates="user")
    support_tickets = relationship("SupportTicket", back_populates="user")
    package_changes = relationship("PackageChange", back_populates="user")
    # conversations = relationship("Conversation", back_populates="user")  # Commented out due to String ID issue
    technician_visits = relationship("TechnicianVisit", back_populates="user")
