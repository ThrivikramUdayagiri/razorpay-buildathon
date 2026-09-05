from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.integrations import get_razorpay_adapter
from app.services.event_normalizer import EventNormalizer
from app.services.ai_gatekeeper import AIGatekeeper
from app.services.policy_engine import PolicyEngine
from app.engines.autopay_engine import AutoPayEngine
from app.engines.checkout_recovery_engine import CheckoutRecoveryEngine
from app.models.payment import WebhookEvent, EventStatus
from app.schemas.events import WebhookResponse
from app.services.audit_service import AuditService

router = APIRouter()
ai_gatekeeper = AIGatekeeper()
normalizer = EventNormalizer()

@router.post("/webhooks/razorpay", response_model=WebhookResponse)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    # 1. Read raw body and verify signature
    body = await request.body()
    body_str = body.decode("utf-8")
    
    adapter = get_razorpay_adapter()
    if not adapter.verify_webhook_signature(body_str, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    raw_payload = await request.json()
    headers = dict(request.headers)
    
    # 2. Normalize Event
    normalized_event = normalizer.normalize_razorpay_webhook(raw_payload, headers)
    
    # 3. Idempotency Check
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.event_id == normalized_event.event_id).first()
    if existing_event:
        AuditService.log_event(
            db=db,
            entity_type="Webhook",
            entity_id=normalized_event.event_id,
            event_type="WEBHOOK_DUPLICATE",
            decision="BLOCKED",
            reason="Idempotency constraint"
        )
        return WebhookResponse(status="already_processed", duplicate_event=True)

    # 4. Save initial event
    webhook_record = WebhookEvent(
        event_id=normalized_event.event_id,
        event_type=normalized_event.event_type,
        payload=raw_payload,
        status=EventStatus.PROCESSED
    )
    db.add(webhook_record)
    db.commit()
    
    AuditService.log_event(
        db=db,
        entity_type="Webhook",
        entity_id=normalized_event.event_id,
        event_type="WEBHOOK_RECEIVED",
        decision="PROCESS",
        metadata={"event_type": normalized_event.event_type}
    )

    # Only process failure events for recovery
    if not (normalized_event.event_type.endswith(".failed") or normalized_event.status == "failed"):
        # We might log successful payments in revenue service elsewhere
        return WebhookResponse(status="processed")

    # 5. AI Gatekeeper
    ai_decision = ai_gatekeeper.classify(normalized_event)
    
    AuditService.log_event(
        db=db,
        entity_type="Webhook",
        entity_id=normalized_event.event_id,
        event_type="AI_CLASSIFIED",
        decision=ai_decision.intent,
        reason=ai_decision.reason,
        metadata={"recommended_action": ai_decision.recommended_action, "confidence": ai_decision.confidence}
    )

    # 6. Policy Engine
    policy_decision = PolicyEngine.evaluate(db, normalized_event, ai_decision)
    
    AuditService.log_event(
        db=db,
        entity_type="Webhook",
        entity_id=normalized_event.event_id,
        event_type=f"POLICY_{policy_decision.decision}",
        decision=policy_decision.decision,
        reason=policy_decision.reason
    )

    if policy_decision.decision == "DENIED":
        # Log hard stop
        AuditService.log_event(
            db=db,
            entity_type="Webhook",
            entity_id=normalized_event.event_id,
            event_type="HARD_STOP",
            decision="DENIED_BY_POLICY",
            reason=policy_decision.reason
        )
        return WebhookResponse(status="processed_hard_stop")

    # 7. Route to appropriate Engine
    if normalized_event.subscription_id:
        AutoPayEngine.handle_failure(db, normalized_event, ai_decision)
    else:
        CheckoutRecoveryEngine.handle_failure(db, normalized_event, ai_decision)

    return WebhookResponse(status="processed")
