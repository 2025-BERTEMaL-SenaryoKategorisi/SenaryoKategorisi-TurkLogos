"""
LLM Tools Service - 9 specialized tools for AI agent interaction
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.user_service import EnhancedUserService
from app.services.package_service import PackageService
from app.models.user import User
from app.models.package import Package
from app.models.bill import Bill
from app.models.support_ticket import SupportTicket
from app.models.technicisian_visit import TechnicianVisit
from app.models.package_change import PackageChange

router = APIRouter(prefix="/llm-tools", tags=["LLM Tools"])

# =====================================================
# 🤖 LLM TOOLS FOR AI AGENT
# =====================================================

@router.post("/authenticate_user")
async def authenticate_user_tool(
    phone_number: str,
    tc_kimlik: Optional[str] = None,
    birth_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 1:** User Authentication
    
    Progressive authentication for Turkish telecom customers.
    Used by AI agent to verify customer identity.
    """
    from app.schemas.auth import AuthenticationRequest
    from datetime import date
    
    # Parse birth_date if provided
    birth_date_obj = None
    if birth_date:
        try:
            birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid birth date format. Use YYYY-MM-DD"}
    
    auth_request = AuthenticationRequest(
        phone_number=phone_number,
        tc_kimlik=tc_kimlik,
        birth_date=birth_date_obj
    )
    
    service = EnhancedUserService(db)
    result = service.authenticate_user(auth_request)
    
    return {
        "authenticated": result.authenticated,
        "session_id": result.session_id,
        "user_id": result.user_id,
        "full_name": result.full_name,
        "requires_tc_kimlik": result.requires_tc_kimlik,
        "requires_birth_date": result.requires_birth_date,
        "error_message": result.error_message
    }

@router.get("/get_user_info")
async def get_user_info_tool(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 2:** Get User Information
    
    Retrieve comprehensive user data for authenticated session.
    """
    service = EnhancedUserService(db)
    user_info = service.get_user_info(session_id)
    
    if not user_info:
        return {"error": "Invalid or expired session"}
    
    return user_info.dict()

@router.get("/get_available_packages")
async def get_available_packages_tool(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 3:** Get Available Packages
    
    List all telecom packages with pricing and features.
    Returns personalized package recommendations.
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        return {"error": "Invalid or expired session"}
    
    # Use the enhanced PackageService for personalized recommendations
    packages = PackageService.get_available_packages(user_data['user_id'], db)
    
    return {
        "success": True,
        "packages": packages,
        "total_count": len(packages),
        "personalized": True,
        "message": f"Size özel {len(packages)} paket önerisi hazırlandı."
    }

@router.get("/get_current_bill")
async def get_current_bill_tool(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 4:** Get Current Bill
    
    Retrieve user's current month bill information.
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        return {"error": "Invalid or expired session"}
    
    # Get current month's bill - find bills where current date is within billing period
    current_date = datetime.now().date()
    bill = db.query(Bill).filter(
        Bill.user_id == user_data['user_id'],
        Bill.billing_period_start <= current_date,
        Bill.billing_period_end >= current_date
    ).first()
    
    if not bill:
        return {"error": "No bill found for current month"}
    
    return {
        "bill_id": bill.bill_id,
        "total_amount": bill.total_amount,
        "base_amount": bill.base_amount,
        "usage_charges": bill.usage_charges,
        "taxes": bill.taxes,
        "discounts": bill.discounts,
        "due_date": bill.due_date.isoformat(),
        "payment_status": bill.payment_status,
        "billing_period_start": bill.billing_period_start.isoformat(),
        "billing_period_end": bill.billing_period_end.isoformat(),
        "payment_date": bill.payment_date.isoformat() if bill.payment_date else None,
        "data_used_gb": bill.data_used_gb,
        "voice_used_minutes": bill.voice_used_minutes,
        "sms_used_count": bill.sms_used_count
    }

@router.get("/get_usage_summary")
async def get_usage_summary_tool(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 5:** Get Usage Summary
    
    Current month usage statistics for data and voice.
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        return {"error": "Invalid or expired session"}
    
    user = db.query(User).filter(User.customer_id == user_data['user_id']).first()
    if not user:
        return {"error": "User not found"}
    
    # Get current package limits
    package_limits = {"data_limit_gb": 0, "voice_minutes": 0}
    if user.current_package_id:
        package = db.query(Package).filter(Package.package_id == user.current_package_id).first()
        if package:
            package_limits = {
                "data_limit_gb": package.data_limit_gb,
                "voice_minutes": package.voice_minutes
            }
    
    return {
        "data_usage_gb": user.data_usage_gb,
        "data_limit_gb": package_limits["data_limit_gb"],
        "data_remaining_gb": max(0, package_limits["data_limit_gb"] - user.data_usage_gb),
        "voice_usage_minutes": user.voice_usage_minutes,
        "voice_limit_minutes": package_limits["voice_minutes"],
        "voice_remaining_minutes": max(0, package_limits["voice_minutes"] - user.voice_usage_minutes)
    }

@router.post("/change_package")
async def change_package_tool(
    session_id: str,
    new_package_id: str,
    effective_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 6:** Change Package
    
    Process package change request for authenticated user.
    Uses comprehensive business logic with validation and pricing.
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        return {"error": "Invalid or expired session"}
    
    # Use the enhanced PackageService for comprehensive package change
    result = PackageService.initiate_package_change(
        customer_id=user_data['user_id'],
        package_code=new_package_id,
        session_id=session_id,
        db=db
    )
    
    return result

@router.post("/create_support_ticket")
async def create_support_ticket_tool(
    session_id: str,
    subject: str,
    description: str,
    category: str = "general",
    priority: str = "medium",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 7:** Create Support Ticket
    
    Create support ticket for customer issues.
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        return {"error": "Invalid or expired session"}
    
    import uuid
    ticket = SupportTicket(
        ticket_id=f"TKT-{uuid.uuid4().hex[:8].upper()}",
        customer_id=user_data['user_id'],
        subject=subject,
        description=description,
        category=category,
        priority=priority,
        status="open"
    )
    
    db.add(ticket)
    db.commit()
    
    return {
        "success": True,
        "ticket_id": ticket.ticket_id,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "message": "Support ticket created successfully"
    }

@router.post("/schedule_technician_visit")
async def schedule_technician_visit_tool(
    session_id: str,
    visit_type: str,
    preferred_date: str,
    preferred_time: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 8:** Schedule Technician Visit
    
    Schedule technician visit for installations or repairs.
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        return {"error": "Invalid or expired session"}
    
    # Parse visit date and time
    try:
        visit_datetime = datetime.strptime(f"{preferred_date} {preferred_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Invalid date/time format. Use YYYY-MM-DD and HH:MM"}
    
    import uuid
    visit = TechnicianVisit(
        visit_id=f"VIS-{uuid.uuid4().hex[:8].upper()}",
        customer_id=user_data['user_id'],
        visit_type=visit_type,
        scheduled_date=visit_datetime,
        status="scheduled",
        notes=notes or ""
    )
    
    db.add(visit)
    db.commit()
    
    return {
        "success": True,
        "visit_id": visit.visit_id,
        "scheduled_date": visit.scheduled_date.isoformat(),
        "status": visit.status,
        "message": "Technician visit scheduled successfully"
    }

@router.get("/get_account_balance")
async def get_account_balance_tool(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    **LLM Tool 9:** Get Account Balance
    
    Retrieve current account balance and payment status.
    """
    service = EnhancedUserService(db)
    user_data = service._get_session_data(session_id)
    
    if not user_data:
        return {"error": "Invalid or expired session"}
    
    user = db.query(User).filter(User.customer_id == user_data['user_id']).first()
    if not user:
        return {"error": "User not found"}
    
    return {
        "balance": user.balance,
        "credit_limit": user.credit_limit,
        "available_credit": user.credit_limit + user.balance if user.balance < 0 else user.credit_limit,
        "payment_status": user.payment_status,
        "account_status": user.account_status
    }
