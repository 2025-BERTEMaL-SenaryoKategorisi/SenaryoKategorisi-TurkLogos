"""
Enhanced Authentication API endpoints with progressive authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.services.user_service import EnhancedUserService
from app.services.package_service import PackageService
from app.schemas.auth import (
    AuthenticationRequest, 
    AuthenticationResponse, 
    UserInfoResponse,
    PackageInfo,
    BillInfo
)
from app.models.user import User
from app.models.package import Package
from app.models.bill import Bill

router = APIRouter(prefix="/auth", tags=["Enhanced Authentication"])

# =====================================================
# 🔐 ENHANCED AUTHENTICATION ENDPOINTS
# =====================================================

@router.post("/authenticate", response_model=AuthenticationResponse)
async def authenticate_user(
    auth_request: AuthenticationRequest,
    db: Session = Depends(get_db)
):
    """
    Progressive authentication for Turkish telecom customers.
    
    **Step 1:** Provide phone_number
    **Step 2:** If requires_tc_kimlik=True, provide tc_kimlik  
    **Step 3:** If requires_birth_date=True, provide birth_date
    
    **Security Features:**
    - Account locking after 3 failed attempts
    - TC Kimlik validation (11 digits)
    - Birth date verification
    - Session management with Redis
    """
    service = EnhancedUserService(db)
    return service.authenticate_user(auth_request)

@router.get("/user-info", response_model=UserInfoResponse)
async def get_user_info(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive user information for authenticated session.
    
    **Requires:** Valid session_id from successful authentication
    
    **Returns:**
    - Customer details
    - Current package information
    - Account status and balance
    - Usage statistics
    - Address information
    """
    service = EnhancedUserService(db)
    user_info = service.get_user_info(session_id)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return user_info

@router.get("/packages", response_model=List[PackageInfo])
async def get_available_packages(
    customer_id: str = Header(..., alias="X-Customer-ID"),
    db: Session = Depends(get_db)
):
    """
    Get all available packages for authenticated user.
    
    **Features:**
    - Personalized package recommendations
    - Data limits and pricing
    - Voice minute allowances  
    - Special features (roaming, international calls, etc.)
    - Package suitability analysis
    """
    service = EnhancedUserService(db)
    
    # Get user by customer_id
    user = db.query(User).filter(User.customer_id == customer_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Use enhanced PackageService for personalized recommendations
    enhanced_packages = PackageService.get_available_packages(user.customer_id, db)
    
    # Convert enhanced package data to schema format
    package_list = []
    for pkg_data in enhanced_packages:
        package_info = PackageInfo(
            package_id=pkg_data["id"],
            name=pkg_data["name"],
            description=pkg_data["description"],
            price=pkg_data["monthly_price"],
            data_limit_gb=pkg_data["specifications"]["data_limit_gb"],
            voice_minutes=pkg_data["specifications"]["voice_minutes"],
            sms_count=pkg_data["specifications"]["sms_count"],
            features=pkg_data["features"]
        )
        package_list.append(package_info)
    
    return package_list

@router.get("/bills", response_model=List[BillInfo])
async def get_user_bills(
    session_id: str,
    limit: int = 6,
    db: Session = Depends(get_db)
):
    """
    Get user's billing history.
    
    **Parameters:**
    - limit: Number of recent bills to return (default: 6)
    
    **Returns:**
    - Bill amounts and due dates
    - Payment status
    - Billing periods
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    bills = db.query(Bill).filter(
        Bill.user_id == user_data['user_id']
    ).order_by(Bill.created_at.desc()).limit(limit).all()
    
    return [
        BillInfo(
            bill_id=bill.bill_id,
            billing_period_start=bill.billing_period_start,
            billing_period_end=bill.billing_period_end,
            due_date=bill.due_date,
            base_amount=bill.base_amount,
            usage_charges=bill.usage_charges,
            taxes=bill.taxes,
            discounts=bill.discounts,
            total_amount=bill.total_amount,
            payment_status=bill.payment_status,
            payment_date=bill.payment_date,
            payment_method=bill.payment_method,
            data_used_gb=bill.data_used_gb,
            voice_used_minutes=bill.voice_used_minutes,
            sms_used_count=bill.sms_used_count
        )
        for bill in bills
    ]

@router.post("/logout")
async def logout_user(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate session.
    
    **Security:** Removes session from Redis to prevent reuse
    """
    service = EnhancedUserService(db)
    
    if service.redis_client:
        try:
            service.redis_client.delete(f"session:{session_id}")
        except Exception:
            pass  # Session cleanup failed, but logout should succeed
    
    return {"message": "Successfully logged out"}

@router.get("/validate-session")
async def validate_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Validate if session is still active.
    
    **Use case:** Check session validity before making API calls
    """
    service = EnhancedUserService(db)
    is_valid = service.validate_session(session_id)
    
    return {
        "valid": is_valid,
        "message": "Session is valid" if is_valid else "Session is invalid or expired"
    }
