"""
TEKNOFEST 2025 - Package Service Implementation
Complete business logic for telecom package management
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid
import random
import json
from loguru import logger

from app.models import User, Package, PackageChange
from app.core.database import get_redis

# =====================================================
# 1. PACKAGE SERVICE - Complete Implementation
# =====================================================

class PackageService:
    """Complete package management business logic for TEKNOFEST."""
    
    @staticmethod
    def get_available_packages(user_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Get available packages for customer - TEKNOFEST requirement.
        Returns personalized package recommendations.
        """
        try:
            # Get user information
            user = db.query(User).filter(User.customer_id == user_id).first()
            if not user:
                logger.error(f"User not found for packages: {user_id}")
                return []

            # Get current package details
            current_package = None
            if user.current_package_id:
                current_package = db.query(Package).filter(
                    Package.package_id == user.current_package_id
                ).first()

            # Get all active packages
            all_packages = db.query(Package).filter(
                and_(Package.is_active == True, Package.is_available_for_new == True)
            ).order_by(Package.price).all()

            if not all_packages:
                logger.warning("No packages available")
                return []

            # Build personalized package list
            package_recommendations = []

            for package in all_packages:
                # Skip current package
                if current_package and package.package_id == current_package.package_id:
                    continue

                # Calculate package comparison
                comparison_data = PackageService._compare_packages(current_package, package, user)

                # Build package information
                package_info = {
                    "id": package.package_id,
                    "name": package.name,
                    "description": package.description,
                    "monthly_price": float(package.price),
                    "price_display": f"{package.price:.0f} TL/ay",
                    "currency": package.currency,

                    # Package details
                    "specifications": {
                        "data_limit_gb": package.data_limit_gb,
                        "data_display": "Limitsiz" if package.data_limit_gb == -1 else f"{package.data_limit_gb} GB",
                        "voice_minutes": package.voice_minutes,
                        "voice_display": "Limitsiz" if package.voice_minutes == -1 else f"{package.voice_minutes} dk",
                        "sms_count": package.sms_count,
                        "sms_display": "Limitsiz" if package.sms_count == -1 else f"{package.sms_count} SMS",
                        "internet_speed_mbps": package.internet_speed_mbps,
                        "speed_display": f"{package.internet_speed_mbps} Mbps" if package.internet_speed_mbps else "Standart hız"
                    },

                    # Features and benefits
                    "features": package.features or {},
                    "key_benefits": PackageService._get_package_benefits(package),

                    # Comparison with current package
                    "comparison": comparison_data,

                    # Personalization
                    "recommendation_score": PackageService._calculate_recommendation_score(package, user),
                    "suitability": PackageService._assess_package_suitability(package, user),

                    # Pricing information
                    "pricing_details": {
                        "setup_fee": 0.0,  # No setup fee for demo
                        "early_termination_fee": PackageService._calculate_early_termination_fee(user),
                        "first_month_discount": PackageService._get_first_month_discount(package, user),
                        "total_first_month": PackageService._calculate_first_month_cost(package, user)
                    }
                }

                package_recommendations.append(package_info)

            # Sort by recommendation score (highest first)
            package_recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

            logger.info(f"Retrieved {len(package_recommendations)} personalized packages for user {user_id}")
            return package_recommendations

        except Exception as e:
            logger.error(f"Error getting available packages: {str(e)}")
            return []

    @staticmethod
    def _compare_packages(current_package: Optional[Package], new_package: Package, user: User) -> Dict[str, Any]:
        """Compare new package with current package."""
        if not current_package:
            return {
                "is_upgrade": True,
                "price_difference": new_package.price,
                "price_change_text": f"+{new_package.price:.0f} TL/ay",
                "data_change": f"+{new_package.data_limit_gb if new_package.data_limit_gb > 0 else 'Limitsiz'} GB",
                "voice_change": f"+{new_package.voice_minutes if new_package.voice_minutes > 0 else 'Limitsiz'} dk",
                "overall_change": "Yeni paket"
            }

        price_diff = new_package.price - current_package.price
        is_upgrade = price_diff > 0

        # Data comparison
        if current_package.data_limit_gb == -1:
            data_change = "Aynı (Limitsiz)"
        elif new_package.data_limit_gb == -1:
            data_change = "Limitsiz"
        else:
            data_diff = new_package.data_limit_gb - current_package.data_limit_gb
            data_change = f"+{data_diff} GB" if data_diff > 0 else f"{data_diff} GB"

        # Voice comparison
        if current_package.voice_minutes == -1:
            voice_change = "Aynı (Limitsiz)"
        elif new_package.voice_minutes == -1:
            voice_change = "Limitsiz"
        else:
            voice_diff = new_package.voice_minutes - current_package.voice_minutes
            voice_change = f"+{voice_diff} dk" if voice_diff > 0 else f"{voice_diff} dk"

        # Speed comparison
        speed_change = "Aynı"
        if current_package.internet_speed_mbps and new_package.internet_speed_mbps:
            speed_diff = new_package.internet_speed_mbps - current_package.internet_speed_mbps
            if speed_diff != 0:
                speed_change = f"+{speed_diff} Mbps" if speed_diff > 0 else f"{speed_diff} Mbps"

        return {
            "is_upgrade": is_upgrade,
            "price_difference": price_diff,
            "price_change_text": f"+{price_diff:.0f} TL/ay" if price_diff > 0 else f"{price_diff:.0f} TL/ay",
            "data_change": data_change,
            "voice_change": voice_change,
            "speed_change": speed_change,
            "overall_change": "Upgrade" if is_upgrade else "Downgrade"
        }

    @staticmethod
    def _get_package_benefits(package: Package) -> List[str]:
        """Get key benefits of the package."""
        benefits = []

        # Data benefits
        if package.data_limit_gb == -1:
            benefits.append("Sınırsız internet")
        elif package.data_limit_gb >= 50:
            benefits.append("Yüksek veri limiti")

        # Voice benefits
        if package.voice_minutes == -1:
            benefits.append("Sınırsız konuşma")
        elif package.voice_minutes >= 1000:
            benefits.append("Bol konuşma dakikası")

        # Speed benefits
        if package.internet_speed_mbps and package.internet_speed_mbps >= 100:
            benefits.append("Ultra hızlı internet")
        elif package.internet_speed_mbps and package.internet_speed_mbps >= 50:
            benefits.append("Hızlı internet")

        # Feature benefits
        features = package.features or {}
        if features.get("roaming"):
            benefits.append("Roaming dahil")
        if features.get("hotspot"):
            benefits.append("Hotspot özelliği")
        if features.get("5g"):
            benefits.append("5G desteği")
        if features.get("family_control"):
            benefits.append("Aile kontrol özellikleri")

        # Price benefits
        if package.price <= 60:
            benefits.append("Ekonomik fiyat")

        return benefits[:5]  # Max 5 benefits

    @staticmethod
    def _calculate_recommendation_score(package: Package, user: User) -> float:
        """Calculate recommendation score for personalization."""
        score = 50.0  # Base score

        # Usage-based scoring
        if user.data_usage_gb:
            if package.data_limit_gb == -1:  # Unlimited
                score += 20
            elif user.data_usage_gb > package.data_limit_gb * 0.8:  # Close to limit
                score -= 15
            elif user.data_usage_gb < package.data_limit_gb * 0.5:  # Overprovisioned
                score -= 10
            else:
                score += 10

        # Voice usage scoring
        if user.voice_usage_minutes:
            if package.voice_minutes == -1:  # Unlimited
                score += 15
            elif user.voice_usage_minutes > package.voice_minutes * 0.8:
                score -= 10
            else:
                score += 5

        # Customer type scoring
        if user.customer_type == "corporate":
            if package.price > 100:  # Premium packages for corporate
                score += 15
            features = package.features or {}
            if features.get("5g"):
                score += 10
        else:  # Individual
            if package.price <= 100:  # Reasonable price for individual
                score += 10

        # Payment status scoring
        if user.payment_status == "paid":
            score += 5
        elif user.payment_status == "overdue":
            if package.price < 80:  # Suggest cheaper packages
                score += 15
            else:
                score -= 20

        return max(0, min(100, score))  # Clamp between 0-100

    @staticmethod
    def _assess_package_suitability(package: Package, user: User) -> Dict[str, Any]:
        """Assess package suitability for user."""
        suitability = {
            "overall_rating": "good",  # excellent, good, fair, poor
            "reasons": [],
            "warnings": [],
            "perfect_for": []
        }

        # Usage assessment
        if user.data_usage_gb and package.data_limit_gb > 0:
            usage_ratio = user.data_usage_gb / package.data_limit_gb
            if usage_ratio > 1:
                suitability["warnings"].append("Mevcut kullanımınız bu paket limitini aşıyor")
                suitability["overall_rating"] = "poor"
            elif usage_ratio > 0.9:
                suitability["warnings"].append("Paket limiti kullanımınıza çok yakın")
                suitability["overall_rating"] = "fair"
            elif usage_ratio < 0.3:
                suitability["reasons"].append("Bu paket ihtiyacınızdan fazla olabilir")

        # Budget assessment
        current_balance = user.balance or 0
        if current_balance < 0 and package.price > abs(current_balance):
            suitability["warnings"].append("Mevcut bütçeniz için yüksek olabilir")

        # Feature matching
        if user.customer_type == "corporate":
            features = package.features or {}
            if features.get("5g") and features.get("hotspot"):
                suitability["perfect_for"].append("İş kullanımı")
                suitability["overall_rating"] = "excellent"

        if user.city in ["İstanbul", "Ankara", "İzmir"]:  # Major cities
            if package.internet_speed_mbps and package.internet_speed_mbps >= 100:
                suitability["perfect_for"].append("Büyük şehir kullanımı")

        return suitability

    @staticmethod
    def _calculate_early_termination_fee(user: User) -> float:
        """Calculate early termination fee if applicable."""
        if not user.contract_end_date:
            return 0.0

        remaining_days = (user.contract_end_date - datetime.now()).days
        if remaining_days > 90:  # More than 3 months
            return 75.0  # Fixed early termination fee
        elif remaining_days > 30:  # More than 1 month
            return 25.0
        else:
            return 0.0

    @staticmethod
    def _get_first_month_discount(package: Package, user: User) -> float:
        """Calculate first month discount for new customers."""
        # New customer discount
        if user.customer_type == "individual" and package.price > 80:
            return 20.0  # 20 TL discount
        elif user.customer_type == "corporate":
            return package.price * 0.15  # 15% discount
        else:
            return 10.0  # Standard discount

    @staticmethod
    def _calculate_first_month_cost(package: Package, user: User) -> float:
        """Calculate total first month cost."""
        base_cost = package.price
        early_termination = PackageService._calculate_early_termination_fee(user)
        discount = PackageService._get_first_month_discount(package, user)

        return max(0, base_cost + early_termination - discount)
    
    @staticmethod
    def initiate_package_change(customer_id: str, package_code: str, session_id: str, db: Session) -> Dict[str, Any]:
        """
        Initiate package change with comprehensive business logic - TEKNOFEST requirement.
        """
        try:
            # Comprehensive user validation
            user = db.query(User).filter(User.customer_id == customer_id).first()
            if not user:
                return {
                    "success": False,
                    "error_code": "USER_NOT_FOUND",
                    "message": "Müşteri bilgileri bulunamadı. Lütfen kimlik bilgilerinizi kontrol ediniz."
                }

            # Account status validation
            if user.account_status != "active":
                return {
                    "success": False,
                    "error_code": "ACCOUNT_INACTIVE",
                    "message": f"Hesabınız {user.account_status} durumunda. Paket değişikliği yapabilmek için müşteri hizmetleri ile iletişime geçiniz."
                }

            # New package validation
            new_package = db.query(Package).filter(Package.package_id == package_code).first()
            if not new_package:
                return {
                    "success": False,
                    "error_code": "PACKAGE_NOT_FOUND",
                    "message": "Seçilen paket bulunamadı. Lütfen geçerli bir paket seçiniz."
                }

            if not new_package.is_active or not new_package.is_available_for_new:
                return {
                    "success": False,
                    "error_code": "PACKAGE_UNAVAILABLE",
                    "message": "Seçilen paket şu anda aktif değil. Lütfen başka bir paket seçiniz."
                }

            # Same package validation
            if user.current_package_id == package_code:
                return {
                    "success": False,
                    "error_code": "SAME_PACKAGE",
                    "message": "Zaten bu paketi kullanıyorsunuz. Farklı bir paket seçiniz."
                }

            # Get current package details
            current_package = None
            if user.current_package_id:
                current_package = db.query(Package).filter(
                    Package.package_id == user.current_package_id
                ).first()

            # Payment status validation
            if user.payment_status == "overdue":
                outstanding_amount = abs(user.balance) if user.balance < 0 else 0
                return {
                    "success": False,
                    "error_code": "PAYMENT_OVERDUE",
                    "message": f"Ödenmemiş {outstanding_amount:.2f} TL faturanız bulunmaktadır. Paket değişikliği için önce ödeme yapmanız gerekmektedir.",
                    "outstanding_amount": outstanding_amount
                }

            # Contract and early termination analysis
            early_termination_fee = 0.0
            contract_warning = None

            if user.contract_end_date and user.contract_end_date > datetime.now():
                remaining_days = (user.contract_end_date - datetime.now()).days
                remaining_months = remaining_days / 30

                if remaining_months > 6:  # More than 6 months
                    early_termination_fee = 100.0
                    contract_warning = f"Sözleşmenizin bitmesine {remaining_days} gün var. Erken geçiş ücreti uygulanacaktır."
                elif remaining_months > 3:  # 3-6 months
                    early_termination_fee = 50.0
                    contract_warning = f"Sözleşmenizin bitmesine {remaining_days} gün var. Kısmi erken geçiş ücreti uygulanacaktır."
                elif remaining_months > 1:  # 1-3 months
                    early_termination_fee = 25.0
                    contract_warning = f"Sözleşmenizin bitmesine {remaining_days} gün var."

            # Calculate pricing changes
            old_price = current_package.price if current_package else 0.0
            new_price = new_package.price
            price_difference = new_price - old_price

            # First month cost calculation
            first_month_discount = PackageService._get_first_month_discount(new_package, user)
            first_month_cost = max(0, new_price + early_termination_fee - first_month_discount)

            # Usage compatibility check
            usage_warnings = []
            if user.data_usage_gb and new_package.data_limit_gb > 0:
                if user.data_usage_gb > new_package.data_limit_gb:
                    usage_warnings.append(f"Mevcut {user.data_usage_gb:.1f} GB kullanımınız yeni paket limitini ({new_package.data_limit_gb} GB) aşıyor.")

            if user.voice_usage_minutes and new_package.voice_minutes > 0:
                if user.voice_usage_minutes > new_package.voice_minutes:
                    usage_warnings.append(f"Mevcut {user.voice_usage_minutes} dk konuşma kullanımınız yeni paket limitini ({new_package.voice_minutes} dk) aşıyor.")

            # Create package change record
            change_id = f"PC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
            effective_date = datetime.now() + timedelta(hours=24)  # 24 hours later

            package_change = PackageChange(
                change_id=change_id,
                user_id=user.id,
                old_package_id=user.current_package_id,
                new_package_id=package_code,
                change_reason="customer_request_via_agent",
                old_price=old_price,
                new_price=new_price,
                price_difference=price_difference,
                status="approved",  # Auto-approve for demo
                effective_date=effective_date,
                processed_by="ai_agent",
                session_id=session_id
            )

            db.add(package_change)

            # Update user's current package (for demo - immediate activation)
            old_package_name = current_package.name if current_package else "Mevcut paket"
            user.current_package_id = package_code
            user.updated_at = datetime.now()

            # Update balance with early termination fee if applicable
            if early_termination_fee > 0:
                user.balance = (user.balance or 0) - early_termination_fee

            db.commit()

            # Build comprehensive success response
            success_message = f"🎉 Paket değişikliğiniz başarıyla tamamlandı!\n\n"
            success_message += f"📦 Eski Paket: {old_package_name}\n"
            success_message += f"📦 Yeni Paket: {new_package.name}\n\n"

            if price_difference > 0:
                success_message += f"💰 Aylık ücretiniz {price_difference:.0f} TL artacak (yeni: {new_price:.0f} TL/ay)\n"
            elif price_difference < 0:
                success_message += f"💰 Aylık ücretinizde {abs(price_difference):.0f} TL tasarruf (yeni: {new_price:.0f} TL/ay)\n"
            else:
                success_message += f"💰 Aylık ücretiniz değişmiyor ({new_price:.0f} TL/ay)\n"

            if early_termination_fee > 0:
                success_message += f"⚠️ Erken geçiş ücreti: {early_termination_fee:.0f} TL\n"

            if first_month_discount > 0:
                success_message += f"🎁 İlk ay indirimi: {first_month_discount:.0f} TL\n"

            success_message += f"\n📅 Paketiniz şu anda aktifleştirildi."

            # Prepare response data
            response_data = {
                "success": True,
                "change_id": change_id,
                "message": success_message,

                # Package information
                "package_change": {
                    "old_package": {
                        "id": current_package.package_id if current_package else None,
                        "name": old_package_name,
                        "price": old_price
                    },
                    "new_package": {
                        "id": new_package.package_id,
                        "name": new_package.name,
                        "price": new_price,
                        "description": new_package.description
                    }
                },

                # Financial details
                "financial_impact": {
                    "old_monthly_price": old_price,
                    "new_monthly_price": new_price,
                    "monthly_difference": price_difference,
                    "early_termination_fee": early_termination_fee,
                    "first_month_discount": first_month_discount,
                    "first_month_total": first_month_cost,
                    "annual_cost_change": price_difference * 12
                },

                # Timeline
                "timeline": {
                    "requested_at": datetime.now().isoformat(),
                    "effective_date": effective_date.isoformat(),
                    "next_billing_date": (datetime.now() + timedelta(days=30)).isoformat()
                },

                # Warnings and notifications
                "notifications": {
                    "contract_warning": contract_warning,
                    "usage_warnings": usage_warnings,
                    "next_steps": [
                        "Yeni paket özellikleri hesabınızda görünecek",
                        "İlk fatura yeni paket ücreti ile gelecek",
                        "Paket değişikliği SMS ile onaylanacak"
                    ]
                }
            }

            logger.info(f"Package change completed successfully: {customer_id} -> {package_code}")
            return response_data

        except Exception as e:
            db.rollback()
            logger.error(f"Error in package change: {str(e)}")
            return {
                "success": False,
                "error_code": "SYSTEM_ERROR",
                "message": "Paket değişikliği sırasında sistem hatası oluştu. Lütfen tekrar deneyiniz veya müşteri hizmetleri ile iletişime geçiniz.",
                "technical_error": str(e)
            }

    @staticmethod
    def get_package_comparison(package_ids: List[str], user_id: str, db: Session) -> Dict[str, Any]:
        """
        Compare multiple packages side by side.
        Additional feature for better user experience.
        """
        try:
            user = db.query(User).filter(User.customer_id == user_id).first()
            if not user:
                return {"error": "User not found"}

            packages = db.query(Package).filter(Package.package_id.in_(package_ids)).all()
            if not packages:
                return {"error": "No packages found"}

            comparison = {
                "user_info": {
                    "customer_id": user.customer_id,
                    "current_package": user.current_package_id,
                    "usage_profile": {
                        "data_usage_gb": user.data_usage_gb,
                        "voice_usage_minutes": user.voice_usage_minutes
                    }
                },
                "packages": [],
                "comparison_matrix": {},
                "recommendations": []
            }

            # Build package comparison
            for package in packages:
                package_data = {
                    "id": package.package_id,
                    "name": package.name,
                    "price": package.price,
                    "data_limit": package.data_limit_gb,
                    "voice_minutes": package.voice_minutes,
                    "speed": package.internet_speed_mbps,
                    "features": package.features or {},
                    "recommendation_score": PackageService._calculate_recommendation_score(package, user)
                }
                comparison["packages"].append(package_data)

            # Sort by recommendation score
            comparison["packages"].sort(key=lambda x: x["recommendation_score"], reverse=True)

            # Add best choice recommendation
            if comparison["packages"]:
                best_package = comparison["packages"][0]
                comparison["recommendations"].append(f"Size en uygun paket: {best_package['name']}")

            return comparison

        except Exception as e:
            logger.error(f"Error in package comparison: {str(e)}")
            return {"error": "Comparison service error"}
