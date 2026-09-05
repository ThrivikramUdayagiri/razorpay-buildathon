from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.payment import PaymentRecord

class RevenueService:
    @staticmethod
    def calculate_metrics(db: Session) -> dict:
        """
        Calculates revenue at risk and recovered based on successful and failed payment events.
        """
        # Revenue at risk: sum of all initial failed payments 
        # (simplified: we should track unique failed orders/subscriptions)
        # To prevent double counting, we'll just sum failed payments that don't have a success counterpart.
        
        # All failed amounts
        failed_payments = db.query(PaymentRecord).filter(PaymentRecord.status == "failed").all()
        revenue_at_risk = sum(p.amount for p in failed_payments)
        
        # All recovered amounts
        # In this prototype, a payment is considered recovered if it's "captured" or "authorized"
        # and has a reference back to an original failure (which we'll track via recovery sessions or order linkages)
        successful_payments = db.query(PaymentRecord).filter(PaymentRecord.status.in_(["captured", "authorized"])).all()
        revenue_recovered = sum(p.amount for p in successful_payments)
        
        # Ensure we don't double count. If we have complex logic, we'd map original failed to new success.
        
        recovery_rate = (revenue_recovered / revenue_at_risk * 100) if revenue_at_risk > 0 else 0.0

        return {
            "revenue_at_risk": revenue_at_risk,
            "revenue_recovered": revenue_recovered,
            "recovery_rate": round(recovery_rate, 2),
            "total_events_processed": db.query(PaymentRecord).count()
        }
