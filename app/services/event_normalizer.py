import json
import hashlib
from datetime import datetime
from app.schemas.events import NormalizedPaymentEvent

class EventNormalizer:
    @staticmethod
    def normalize_razorpay_webhook(raw_payload: dict, webhook_headers: dict = None) -> NormalizedPaymentEvent:
        """
        Normalizes an incoming Razorpay webhook payload into our internal structure.
        """
        event_type = raw_payload.get("event", "unknown")
        account_id = raw_payload.get("account_id", "")
        
        # Determine the primary entity (payment, order, subscription)
        payload_data = raw_payload.get("payload", {})
        
        payment = payload_data.get("payment", {}).get("entity", {})
        order = payload_data.get("order", {}).get("entity", {})
        subscription = payload_data.get("subscription", {}).get("entity", {})

        # Extract core fields based on event type
        # For a payment.failed event, we look at payment entity
        payment_id = payment.get("id", "")
        order_id = payment.get("order_id") or order.get("id")
        subscription_id = payment.get("subscription_id") or subscription.get("id")
        customer_id = payment.get("customer_id")
        
        # Amount in INR paise to Float
        amount = payment.get("amount", 0) / 100.0 if "amount" in payment else 0.0
        currency = payment.get("currency", "INR")
        
        status = payment.get("status", "unknown")
        failure_code = payment.get("error_code")
        failure_description = payment.get("error_description")
        
        # Extra context
        mandate_state = "active" if subscription_id else None # simplification for prototype
        if event_type == "subscription.charged" and status == "failed":
            pass # Handle specific sub failure if needed
            
        # Create a hash of the raw payload for tamper-evidence/audit
        raw_payload_str = json.dumps(raw_payload, sort_keys=True)
        payload_hash = hashlib.sha256(raw_payload_str.encode('utf-8')).hexdigest()
        
        # Usually webhooks have a Razorpay Event ID in headers 'x-razorpay-event-id', fallback to hash
        event_id = "evt_" + payload_hash[:16]
        if webhook_headers:
            header_id = webhook_headers.get("x-razorpay-event-id") or webhook_headers.get("X-Razorpay-Event-Id")
            if header_id:
                event_id = header_id

        return NormalizedPaymentEvent(
            event_id=event_id,
            event_type=event_type,
            occurred_at=datetime.utcnow(),
            merchant_id=account_id,
            customer_id=customer_id,
            payment_id=payment_id,
            order_id=order_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            status=status,
            failure_code=failure_code,
            failure_description=failure_description,
            mandate_state=mandate_state,
            raw_payload_hash=payload_hash
        )
