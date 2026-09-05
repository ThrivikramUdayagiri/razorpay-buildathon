from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import hashlib
from app.schemas.events import NormalizedPaymentEvent, AIDecision
from app.models.recovery import RecoverySession, RecoverySessionStatus
from app.models.audit import NotificationEvent
from app.services.audit_service import AuditService

class CheckoutRecoveryEngine:
    @staticmethod
    def handle_failure(
        db: Session, 
        event: NormalizedPaymentEvent, 
        ai_decision: AIDecision
    ):
        """
        Handles Engine B: Context-Aware One-Off Checkout Recovery.
        Never blindly reuse an old payment amount. Creates a local recovery session.
        """
        if ai_decision.recommended_action == "CREATE_RESUME_SESSION":
             # Create a secure token
             raw_token = secrets.token_urlsafe(32)
             token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
             
             # Calculate expiry
             expires_at = datetime.utcnow() + timedelta(hours=24)
             
             session = RecoverySession(
                 token_hash=token_hash,
                 customer_id=event.customer_id or "guest",
                 original_order_id=event.order_id,
                 original_amount=event.amount,
                 current_amount=event.amount, # Initial assumption, re-verified at resume time
                 expires_at=expires_at,
                 status=RecoverySessionStatus.ACTIVE
             )
             db.add(session)
             db.commit()
             db.refresh(session)
             
             AuditService.log_event(
                db=db,
                entity_type="RecoverySession",
                entity_id=str(session.id),
                event_type="RECOVERY_SESSION_CREATED",
                decision="CREATE_RESUME_SESSION",
                reason=ai_decision.reason,
                metadata={"original_order_id": event.order_id}
            )
             
             if ai_decision.customer_contact_allowed:
                 notif = NotificationEvent(
                    template_id="PAYMENT_RESUME_TEMPLATE",
                    channel="EMAIL",
                    recipient_reference=event.customer_id or "unknown",
                    reason="Sending cart resume link."
                 )
                 db.add(notif)
                 db.commit()
                 
             return raw_token # We'd send this to the customer via email/SMS

        elif ai_decision.recommended_action == "INVALIDATE_RECOVERY":
             session = db.query(RecoverySession).filter(
                 RecoverySession.original_order_id == event.order_id,
                 RecoverySession.status == RecoverySessionStatus.ACTIVE
             ).first()
             if session:
                 session.status = RecoverySessionStatus.INVALIDATED
                 db.commit()
                 AuditService.log_event(
                    db=db,
                    entity_type="RecoverySession",
                    entity_id=str(session.id),
                    event_type="RECOVERY_SESSION_INVALIDATED",
                    decision="INVALIDATE_RECOVERY",
                    reason=ai_decision.reason
                )
