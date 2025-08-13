"""
Enhanced User Service for authentication and user management
"""
import json
import redis
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid
from loguru import logger

from app.models.user import User
from app.models.package import Package
from app.models.bill import Bill
from app.models.support_ticket import SupportTicket
from app.schemas.auth import AuthenticationRequest, AuthenticationResponse, SessionData, UserInfoResponse
from app.core.config import settings

class EnhancedUserService:
    """Enhanced user service with Turkish telecom authentication features."""
    
    def __init__(self, db: Session):
        self.db = db
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
        self.session_timeout = 3600  # 1 hour

    def authenticate_user(self, auth_request: AuthenticationRequest) -> AuthenticationResponse:
        """
        Progressive authentication flow for Turkish telecom customers.
        Step 1: Phone number
        Step 2: TC Kimlik
        Step 3: Birth date
        """
        try:
            # Check if user is temporarily locked
            if self._is_user_locked(auth_request.phone_number):
                return AuthenticationResponse(
                    authenticated=False,
                    error_message="Account temporarily locked due to failed attempts",
                    retry_after=300  # 5 minutes
                )
            
            # Find user by phone number
            user = self.db.query(User).filter(User.phone_number == auth_request.phone_number).first()
            if not user:
                self._record_failed_attempt(auth_request.phone_number)
                return AuthenticationResponse(
                    authenticated=False,
                    error_message="Phone number not found in system"
                )
            
            # Progressive authentication logic
            if not auth_request.tc_kimlik:
                return AuthenticationResponse(
                    authenticated=False,
                    requires_tc_kimlik=True,
                    error_message="TC Kimlik required for authentication"
                )
            
            if auth_request.tc_kimlik != user.tc_kimlik:
                self._record_failed_attempt(auth_request.phone_number)
                return AuthenticationResponse(
                    authenticated=False,
                    error_message="TC Kimlik does not match"
                )
            
            if not auth_request.birth_date:
                return AuthenticationResponse(
                    authenticated=False,
                    requires_birth_date=True,
                    error_message="Birth date required for verification"
                )
            
            if auth_request.birth_date != user.birth_date:
                self._record_failed_attempt(auth_request.phone_number)
                return AuthenticationResponse(
                    authenticated=False,
                    error_message="Birth date does not match"
                )
            
            # Successful authentication
            session_id = self._create_session(user)
            self._clear_failed_attempts(auth_request.phone_number)
            
            return AuthenticationResponse(
                authenticated=True,
                session_id=session_id,
                user_id=user.customer_id,
                full_name=f"{user.first_name} {user.last_name}",
                phone_number=user.phone_number
            )
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthenticationResponse(
                authenticated=False,
                error_message=f"Authentication error: {str(e)}"
            )

    def get_user_info(self, session_id: str) -> Optional[UserInfoResponse]:
        """Get comprehensive user information for authenticated session."""
        user_data = self._get_session_data(session_id)
        if not user_data:
            return None
        
        user = self.db.query(User).filter(User.customer_id == user_data['user_id']).first()
        if not user:
            return None
        
        # Get current package info
        package_name = None
        if user.current_package_id:
            package = self.db.query(Package).filter(Package.package_id == user.current_package_id).first()
            if package:
                package_name = package.name
        
        return UserInfoResponse(
            customer_id=user.customer_id,
            phone_number=user.phone_number,
            full_name=f"{user.first_name} {user.last_name}",
            email=user.email,
            account_status=user.account_status,
            customer_type=user.customer_type,
            current_package_name=package_name,
            contract_end_date=user.contract_end_date,
            payment_status=user.payment_status,
            balance=user.balance,
            data_usage_gb=user.data_usage_gb,
            voice_usage_minutes=user.voice_usage_minutes,
            address=user.address,
            city=user.city
        )

    def _create_session(self, user: User) -> str:
        """Create a new session in Redis."""
        session_id = str(uuid.uuid4())
        
        session_data = {
            'user_id': user.customer_id,
            'phone_number': user.phone_number,
            'full_name': f"{user.first_name} {user.last_name}",
            'authenticated_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"session:{session_id}",
                    self.session_timeout,
                    json.dumps(session_data)
                )
            except Exception as e:
                logger.warning(f"Failed to store session in Redis: {e}")
        
        return session_id

    def _get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis."""
        if not self.redis_client:
            return None
            
        try:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                return json.loads(session_data)
        except Exception as e:
            logger.warning(f"Failed to get session from Redis: {e}")
        return None

    def _is_user_locked(self, phone_number: str) -> bool:
        """Check if user is temporarily locked due to failed attempts."""
        user = self.db.query(User).filter(User.phone_number == phone_number).first()
        if user and user.account_locked_until:
            return datetime.now() < user.account_locked_until
        return False

    def _record_failed_attempt(self, phone_number: str):
        """Record a failed authentication attempt."""
        user = self.db.query(User).filter(User.phone_number == phone_number).first()
        if user:
            user.failed_auth_attempts = (user.failed_auth_attempts or 0) + 1
            user.last_auth_attempt = datetime.now()
            
            # Lock account after 3 failed attempts
            if user.failed_auth_attempts >= 3:
                user.account_locked_until = datetime.now() + timedelta(minutes=5)
            
            self.db.commit()

    def _clear_failed_attempts(self, phone_number: str):
        """Clear failed authentication attempts after successful login."""
        user = self.db.query(User).filter(User.phone_number == phone_number).first()
        if user:
            user.failed_auth_attempts = 0
            user.account_locked_until = None
            user.last_auth_attempt = datetime.now()
            self.db.commit()

    def validate_session(self, session_id: str) -> bool:
        """Validate if session is still active."""
        return self._get_session_data(session_id) is not None


# =====================================================
# Legacy UserService for backward compatibility
# =====================================================

class UserService:
    """Legacy user service for backward compatibility."""
    
    @staticmethod
    def authenticate_user(identifier: str, db: Session) -> Union[Dict[str, Any], None]:
        """Legacy authentication method."""
        try:
            user = db.query(User).filter(
                or_(
                    User.phone_number == identifier,
                    User.customer_id == identifier
                )
            ).first()
            
            if not user:
                logger.warning(f"User not found: {identifier}")
                return None
            
            if user.account_status != "active":
                logger.warning(f"User account not active: {identifier}")
                return {
                    "error": "account_inactive",
                    "message": f"Hesabınız {user.account_status} durumunda."
                }
            
            return {
                "user_id": user.customer_id,
                "phone_number": user.phone_number,
                "full_name": f"{user.first_name} {user.last_name}",
                "account_status": user.account_status,
                "balance": user.balance,
                "package_id": user.current_package_id
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
            user_data = {
                "customer_id": user.customer_id,
                "phone_number": user.phone_number,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "account_status": user.account_status,
                "customer_type": user.customer_type,
                "current_package_id": user.current_package_id,
                "contract_end_date": user.contract_end_date.isoformat() if user.contract_end_date else None,
                "payment_status": user.payment_status,
                "balance": float(user.balance),
                "city": user.city,
                "data_usage_gb": float(user.data_usage_gb),
                "voice_usage_minutes": user.voice_usage_minutes
            }
            
            logger.info(f"User authenticated successfully: {user.customer_id}")
            return user_data
            
        except Exception as e:
            logger.error(f"Error in user authentication: {str(e)}")
            return None
    
    @staticmethod
    def get_user_summary(customer_id: str, db: Session) -> Dict[str, Any]:
        """Müşteri özet bilgileri."""
        try:
            user = db.query(User).filter(User.customer_id == customer_id).first()
            if not user:
                return {"error": "User not found"}
            
            # Son fatura
            last_bill = db.query(Bill).filter(Bill.user_id == user.id).order_by(desc(Bill.billing_period_end)).first()
            
            # Aktif destek talepleri
            active_tickets = db.query(SupportTicket).filter(
                and_(SupportTicket.user_id == user.id, SupportTicket.status.in_(["open", "in_progress"]))
            ).count()
            
            return {
                "customer_info": {
                    "name": f"{user.first_name} {user.last_name}",
                    "customer_id": user.customer_id,
                    "account_status": user.account_status,
                    "current_package": user.current_package_id,
                },
                "financial_summary": {
                    "balance": float(user.balance),
                    "payment_status": user.payment_status,
                    "last_bill_amount": float(last_bill.total_amount) if last_bill else 0.0,
                    "last_bill_due": last_bill.due_date.isoformat() if last_bill else None
                },
                "support_summary": {
                    "active_tickets": active_tickets,
                    "last_update": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user summary: {str(e)}")
            return {"error": "Internal error"}