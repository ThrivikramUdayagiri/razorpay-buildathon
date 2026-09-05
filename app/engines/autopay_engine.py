from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.schemas.events import NormalizedPaymentEvent, AIDecision
from app.models.recovery import RecoveryAttempt
from app.models.audit import NotificationEvent
from app.services.audit_service import AuditService

class AutoPayEngine:
    @staticmethod
    def handle_failure(
        db: Session, 
        event: NormalizedPaymentEvent, 
        ai_decision: AIDecision
    ):
        """
        Handles Engine A: Recurring Mandate / AutoPay Recovery.
        """
        # If policy denied or AI suggested hard stop, we do nothing more proactively
        if ai_decision.recommended_action == "HARD_STOP":
            return
            
        if ai_decision.recommended_action == "DELAY_RETRY":
            delay = ai_decision.delay_hours or 48
            scheduled_time = datetime.utcnow() + timedelta(hours=delay)
            
            attempt = RecoveryAttempt(
                subscription_id=event.subscription_id,
                customer_id=event.customer_id,
                reason=ai_decision.reason,
                scheduled_at=scheduled_time,
                status="SCHEDULED"
            )
            db.add(attempt)
            db.commit()
            
            AuditService.log_event(
                db=db,
                entity_type="Subscription",
                entity_id=event.subscription_id,
                event_type="RETRY_SCHEDULED",
                decision="DELAY_RETRY",
                reason=ai_decision.reason,
                metadata={"delay_hours": delay, "scheduled_at": scheduled_time.isoformat()}
            )
            
            if ai_decision.customer_contact_allowed:
                # Simulate sending a notification
                notif = NotificationEvent(
                    template_id="PAYMENT_RECOVERY_TEMPLATE",
                    channel="EMAIL",
                    recipient_reference=event.customer_id or "unknown",
                    reason="Notifying of failed autopay, retry scheduled."
                )
                db.add(notif)
                db.commit()

        elif ai_decision.recommended_action == "GENERATE_PAYMENT_LINK":
             # In a full implementation, we'd call RazorpayAdapter to create link
             # For the prototype, we simulate it
             AuditService.log_event(
                db=db,
                entity_type="Subscription",
                entity_id=event.subscription_id,
                event_type="PAYMENT_LINK_CREATED",
                decision="GENERATE_PAYMENT_LINK",
                reason=ai_decision.reason
            )
             if ai_decision.customer_contact_allowed:
                notif = NotificationEvent(
                    template_id="PAYMENT_LINK_TEMPLATE",
                    channel="EMAIL",
                    recipient_reference=event.customer_id or "unknown",
                    reason="Sending alternate payment link for autopay failure."
                )
                db.add(notif)
                db.commit()
