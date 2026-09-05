from sqlalchemy.orm import Session
from app.schemas.events import NormalizedPaymentEvent, AIDecision, PolicyDecision
from app.models.payment import PaymentRecord
from app.models.recovery import RecoverySession, RecoverySessionStatus
from app.config import settings

class PolicyEngine:
    @staticmethod
    def evaluate(
        db: Session, 
        event: NormalizedPaymentEvent, 
        ai_decision: AIDecision
    ) -> PolicyDecision:
        """
        Evaluates the AI decision against hard business rules and DB state.
        Returns AUTHORIZED or DENIED.
        """
        
        # 1. Hard Stop: Mandate Revoked
        if ai_decision.reason == "MANDATE_REVOKED" or (event.failure_code == "BAD_REQUEST_ERROR" and "mandate" in str(event.failure_description).lower()):
            return PolicyDecision(decision="DENIED", reason="MANDATE_REVOKED")

        # 2. Hard Stop: Already Paid
        # Check if the customer/order/subscription already has a successful payment recently
        if event.order_id:
            successful_payment = db.query(PaymentRecord).filter(
                PaymentRecord.order_id == event.order_id,
                PaymentRecord.status.in_(["authorized", "captured"])
            ).first()
            if successful_payment:
                 return PolicyDecision(decision="DENIED", reason="ALREADY_PAID")

        # 3. Hard Stop: Max Touchpoints
        if event.order_id or event.subscription_id:
             # Find existing recovery session
             session = db.query(RecoverySession).filter(
                 (RecoverySession.original_order_id == event.order_id) | 
                 (RecoverySession.customer_id == event.customer_id)
             ).first()
             
             if session and session.touch_count >= settings.max_recovery_touchpoints:
                 return PolicyDecision(decision="DENIED", reason="MAX_TOUCHPOINTS_EXCEEDED")

        # 4. Hard Stop: Session Invalidated
        if event.order_id:
             session = db.query(RecoverySession).filter(
                 RecoverySession.original_order_id == event.order_id,
                 RecoverySession.status != RecoverySessionStatus.ACTIVE
             ).first()
             if session:
                  return PolicyDecision(decision="DENIED", reason="SESSION_INVALIDATED")

        # If it passes all hard stops, we authorize the AI's intended action, 
        # unless it was NO_ACTION
        if ai_decision.intent in ["NO_ACTION", "HARD_STOP", "INVALIDATE"]:
            # Policy agrees with AI to not do anything proactive, but it's an "authorized" inaction
            return PolicyDecision(decision="AUTHORIZED", reason="AI_INTENT_RESPECTED")

        return PolicyDecision(decision="AUTHORIZED", reason="POLICY_CHECK_PASSED")
