"""
Data service for initializing sample data with enhanced authentication fields
"""
from datetime import datetime, date
from loguru import logger
from app.core.database import SessionLocal
from app.models.user import User
from app.models.package import Package
from app.models.bill import Bill
from app.models.support_ticket import SupportTicket

async def initialize_sample_data():
    """Initialize sample data with enhanced authentication fields."""
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(User).first():
            logger.info("📋 Sample data already exists")
            return
        
        logger.info("🔄 Creating sample data with enhanced authentication...")
        
        # Create sample packages
        packages = [
            Package(
                package_id="PKG001",
                name="Basic Plan",
                description="Essential mobile package",
                price=49.99,
                data_limit_gb=5,
                voice_minutes=300,
                sms_count=1000,
                features={"sms": "unlimited", "roaming": False}
            ),
            Package(
                package_id="PKG002", 
                name="Premium Plan",
                description="High-speed unlimited package",
                price=99.99,
                data_limit_gb=50,
                voice_minutes=1000,
                sms_count=-1,
                features={"sms": "unlimited", "roaming": True, "international": True}
            ),
            Package(
                package_id="PKG003",
                name="Family Plan",
                description="Family sharing package",
                price=149.99,
                data_limit_gb=100,
                voice_minutes=2000,
                sms_count=-1,
                features={"sms": "unlimited", "roaming": True, "family_sharing": True}
            )
        ]
        
        for package in packages:
            db.add(package)
        
        # Create sample users with enhanced authentication fields
        users = [
            User(
                customer_id="CUST001",
                phone_number="+905551234567",
                first_name="Ahmet",
                last_name="Yılmaz", 
                email="ahmet.yilmaz@email.com",
                tc_kimlik="12345678901",  # 🔐 TC Kimlik
                birth_date=date(1985, 3, 15),  # 🔐 Birth Date
                current_package_id="PKG001",
                balance=25.50,
                data_usage_gb=2.5,
                voice_usage_minutes=150,
                address="Atatürk Cad. No: 123",
                city="İstanbul",
                region="Marmara"
            ),
            User(
                customer_id="CUST002",
                phone_number="+905559876543",
                first_name="Fatma",
                last_name="Demir",
                email="fatma.demir@email.com", 
                tc_kimlik="98765432109",  # 🔐 TC Kimlik
                birth_date=date(1990, 7, 22),  # 🔐 Birth Date
                current_package_id="PKG002",
                balance=-15.25,
                payment_status="overdue",
                data_usage_gb=35.2,
                voice_usage_minutes=750,
                address="İnönü Sok. No: 45",
                city="Ankara",
                region="İç Anadolu"
            ),
            User(
                customer_id="CUST003",
                phone_number="+905556667788",
                first_name="Mehmet",
                last_name="Kaya",
                email="mehmet.kaya@email.com",
                tc_kimlik="11223344556",  # 🔐 TC Kimlik
                birth_date=date(1978, 12, 5),  # 🔐 Birth Date
                current_package_id="PKG003",
                balance=150.75,
                data_usage_gb=75.8,
                voice_usage_minutes=1200,
                customer_type="corporate",
                address="Cumhuriyet Mah. No: 67",
                city="İzmir",
                region="Ege"
            )
        ]
        
        for user in users:
            db.add(user)
        
        # Create sample bills
        bills = [
            Bill(
                bill_id="BILL001",
                billing_period_start=datetime(2024, 11, 1),
                billing_period_end=datetime(2024, 11, 30),
                base_amount=49.99,
                total_amount=49.99,
                due_date=datetime(2024, 12, 15),
                payment_status="paid",
                payment_date=datetime(2024, 11, 20)
            ),
            Bill(
                bill_id="BILL002", 
                billing_period_start=datetime(2024, 11, 1),
                billing_period_end=datetime(2024, 11, 30),
                base_amount=99.99,
                total_amount=99.99,
                due_date=datetime(2024, 12, 15),
                payment_status="overdue"
            ),
            Bill(
                bill_id="BILL003",
                billing_period_start=datetime(2024, 11, 1),
                billing_period_end=datetime(2024, 11, 30),
                base_amount=149.99,
                total_amount=149.99,
                due_date=datetime(2024, 12, 15),
                payment_status="paid",
                payment_date=datetime(2024, 11, 18)
            )
        ]
        
        for bill in bills:
            db.add(bill)
        
        # Create sample support tickets
        tickets = [
            SupportTicket(
                ticket_id="TKT001",
                issue_type="technical",
                title="İnternet yavaş",
                description="Evde internet bağlantısı çok yavaş.",
                priority="medium",
                status="open"
            ),
            SupportTicket(
                ticket_id="TKT002",
                issue_type="billing",
                title="Fatura itirazı",
                description="Bu ay faturamda hatalı ücretlendirme var.",
                priority="high",
                status="in_progress"
            )
        ]
        
        for ticket in tickets:
            db.add(ticket)
        
        db.commit()
        logger.info("✅ Enhanced sample data created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()
