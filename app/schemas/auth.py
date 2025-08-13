"""
Authentication schemas for the enhanced authentication system
"""
from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional

class AuthenticationRequest(BaseModel):
    """Request model for user authentication with progressive field collection."""
    phone_number: str = Field(..., description="User's phone number")
    tc_kimlik: Optional[str] = Field(None, description="TC Identity Number (11 digits)")
    birth_date: Optional[date] = Field(None, description="Birth date for verification")

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic Turkish phone number validation
        if not v.startswith('+90') and not v.startswith('0'):
            raise ValueError('Phone number must start with +90 or 0')
        return v
    
    @validator('tc_kimlik')
    def validate_tc_kimlik(cls, v):
        if v is not None:
            if len(v) != 11 or not v.isdigit():
                raise ValueError('TC Kimlik must be exactly 11 digits')
        return v

class AuthenticationResponse(BaseModel):
    """Response model for authentication with user data and status."""
    authenticated: bool = Field(..., description="Whether authentication was successful")
    session_id: Optional[str] = Field(None, description="Session ID for authenticated users")
    
    # Progressive authentication fields
    requires_tc_kimlik: bool = Field(False, description="Whether TC kimlik is required")
    requires_birth_date: bool = Field(False, description="Whether birth date is required")
    
    # User data (only if authenticated)
    user_id: Optional[str] = Field(None, description="User's customer ID")
    full_name: Optional[str] = Field(None, description="User's full name")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if authentication failed")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry (if rate limited)")

class SessionData(BaseModel):
    """Session data stored in Redis."""
    user_id: str
    phone_number: str
    full_name: str
    authenticated_at: datetime
    last_activity: datetime
    
    class Config:
        arbitrary_types_allowed = True

class UserInfoResponse(BaseModel):
    """Comprehensive user information response."""
    customer_id: str
    phone_number: str
    full_name: str
    email: str
    account_status: str
    customer_type: str
    current_package_name: Optional[str] = None
    contract_end_date: Optional[datetime] = None
    payment_status: str
    balance: float
    data_usage_gb: float
    voice_usage_minutes: int
    address: Optional[str] = None
    city: Optional[str] = None

class PackageInfo(BaseModel):
    """Package information for user queries."""
    package_id: str
    name: str
    description: str
    price: float
    data_limit_gb: int
    voice_minutes: int
    sms_count: int
    features: dict

class BillInfo(BaseModel):
    """Bill information response."""
    bill_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    due_date: datetime
    base_amount: float
    usage_charges: float
    taxes: float
    discounts: float
    total_amount: float
    payment_status: str
    payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    data_used_gb: float
    voice_used_minutes: int
    sms_used_count: int
