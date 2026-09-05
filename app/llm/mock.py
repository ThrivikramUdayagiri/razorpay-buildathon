from .base import LLMProvider
from app.schemas.events import NormalizedPaymentEvent, AIDecision

class MockProvider(LLMProvider):
    def classify_failure(self, event: NormalizedPaymentEvent) -> AIDecision:
        # Deterministic rules to simulate AI for the demo
        
        if event.failure_code == "BAD_REQUEST_ERROR" and "mandate" in str(event.failure_description).lower():
            return AIDecision(
                intent="HARD_STOP",
                reason="MANDATE_REVOKED",
                recommended_action="HARD_STOP",
                customer_contact_allowed=False,
                confidence=0.99
            )
            
        if event.failure_code == "BAD_REQUEST_ERROR" and "funds" in str(event.failure_description).lower():
            # Smart Scheduling: Wait 72 hours for potential salary deposits
            return AIDecision(
                intent="RECOVER",
                reason="INSUFFICIENT_FUNDS",
                recommended_action="DELAY_RETRY",
                delay_hours=72,
                customer_contact_allowed=True,
                confidence=0.95
            )
            
        if event.failure_code == "GATEWAY_ERROR" and "timeout" in str(event.failure_description).lower():
             # Smart Scheduling: Delay 12 hours to hit off-peak server traffic at night
             return AIDecision(
                intent="RECOVER",
                reason="BANK_TIMEOUT",
                recommended_action="SCHEDULE_RECOVERY",
                delay_hours=12,
                customer_contact_allowed=False,
                confidence=0.90
            )
             
        if not event.subscription_id: # One-off checkout
             return AIDecision(
                intent="RECOVER",
                reason="PAYMENT_FAILED",
                recommended_action="CREATE_RESUME_SESSION",
                customer_contact_allowed=True,
                confidence=0.88
            )

        # Default fallback
        return AIDecision(
            intent="NO_ACTION",
            reason="UNKNOWN",
            recommended_action="NO_ACTION",
            confidence=0.5
        )
