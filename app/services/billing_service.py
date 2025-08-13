class BillingService:
    """Faturalama business logic."""
    
    @staticmethod
    def get_bill_details(customer_id: str, billing_period: Optional[str], db: Session) -> Dict[str, Any]:
        """
        Fatura detaylarını getir - TEKNOFEST gereksinimi.
        """
        try:
            # Kullanıcı kontrolü
            user = db.query(User).filter(User.customer_id == customer_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "Müşteri bulunamadı."
                }
            
            # Fatura sorgusu
            query = db.query(Bill).filter(Bill.user_id == user.id)
            
            if billing_period:
                # Belirli bir dönem sorgulandıysa
                try:
                    year, month = billing_period.split("-")
                    start_date = datetime(int(year), int(month), 1)
                    end_date = datetime(int(year), int(month) + 1, 1) if int(month) < 12 else datetime(int(year) + 1, 1, 1)
                    query = query.filter(
                        and_(Bill.billing_period_start >= start_date, Bill.billing_period_start < end_date)
                    )
                except ValueError:
                    return {"success": False, "error": "Geçersiz fatura dönemi formatı. YYYY-MM formatında giriniz."}
            
            bills = query.order_by(desc(Bill.billing_period_end)).limit(5).all()
            
            if not bills:
                return {
                    "success": False,
                    "error": "Belirtilen dönem için fatura bulunamadı."
                }
            
            # En son fatura bilgileri
            latest_bill = bills[0]
            
            bill_data = {
                "success": True,
                "bill_info": {
                    "bill_id": latest_bill.bill_id,
                    "customer_name": f"{user.first_name} {user.last_name}",
                    "billing_period": f"{latest_bill.billing_period_start.strftime('%d.%m.%Y')} - {latest_bill.billing_period_end.strftime('%d.%m.%Y')}",
                    "due_date": latest_bill.due_date.strftime('%d.%m.%Y'),
                    "payment_status": latest_bill.payment_status,
                    "payment_date": latest_bill.payment_date.strftime('%d.%m.%Y') if latest_bill.payment_date else None
                },
                "amount_breakdown": {
                    "base_amount": float(latest_bill.base_amount),
                    "usage_charges": float(latest_bill.usage_charges),
                    "taxes": float(latest_bill.taxes),
                    "discounts": float(latest_bill.discounts),
                    "total_amount": float(latest_bill.total_amount)
                },
                "usage_details": {
                    "data_used_gb": float(latest_bill.data_used_gb),
                    "voice_used_minutes": latest_bill.voice_used_minutes,
                    "sms_used_count": latest_bill.sms_used_count
                },
                "payment_info": {
                    "can_pay_online": latest_bill.payment_status in ["pending", "overdue"],
                    "payment_methods": ["credit_card", "bank_transfer", "mobile_payment"],
                    "installment_available": float(latest_bill.total_amount) > 100.0
                }
            }
            
            # Ödeme durumuna göre mesaj
            if latest_bill.payment_status == "paid":
                bill_data["message"] = "Faturanız ödenmiştir. Teşekkür ederiz!"
            elif latest_bill.payment_status == "pending":
                days_until_due = (latest_bill.due_date - datetime.now().date()).days
                bill_data["message"] = f"Faturanızın son ödeme tarihi {days_until_due} gün sonra."
            elif latest_bill.payment_status == "overdue":
                days_overdue = (datetime.now().date() - latest_bill.due_date).days
                bill_data["message"] = f"Faturanız {days_overdue} gün gecikmiştir. Lütfen en kısa sürede ödemek için müşteri hizmetleri ile iletişime geçin."
            
            # Son 3 ay fatura özeti
            if len(bills) > 1:
                bill_data["recent_bills"] = []
                for bill in bills[:3]:
                    bill_data["recent_bills"].append({
                        "period": bill.billing_period_start.strftime('%Y-%m'),
                        "amount": float(bill.total_amount),
                        "status": bill.payment_status,
                        "due_date": bill.due_date.strftime('%d.%m.%Y')
                    })
            
            logger.info(f"Bill details retrieved for customer: {customer_id}")
            return bill_data
            
        except Exception as e:
            logger.error(f"Error getting bill details: {str(e)}")
            return {
                "success": False,
                "error": "Fatura bilgileri alınırken bir hata oluştu."
            }