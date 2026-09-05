from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, Dict
from datetime import datetime

class NormalizedPaymentEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime
    merchant_id: str
    customer_id: Optional[str] = None
    payment_id: str
    order_id: Optional[str] = None
    subscription_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    status: str
    failure_code: Optional[str] = None
    failure_description: Optional[str] = None
    mandate_state: Optional[str] = None
    subscription_state: Optional[str] = None
    cart_state: Optional[str] = None
    raw_payload_hash: str

class AIDecision(BaseModel):
    intent: Literal["RECOVER", "DELAY", "HARD_STOP", "INVALIDATE", "NO_ACTION"]
    reason: Literal["INSUFFICIENT_FUNDS", "BANK_TIMEOUT", "MANDATE_REVOKED", "PAYMENT_FAILED", "CART_ABANDONED", "ALREADY_PAID", "STALE_CART", "UNKNOWN"]
    recommended_action: Literal["DELAY_RETRY", "SCHEDULE_RECOVERY", "GENERATE_PAYMENT_LINK", "CREATE_RESUME_SESSION", "INVALIDATE_RECOVERY", "HARD_STOP", "NO_ACTION"]
    delay_hours: Optional[int] = 0
    customer_contact_allowed: bool = False
    confidence: float = Field(ge=0.0, le=1.0)

class PolicyDecision(BaseModel):
    decision: Literal["AUTHORIZED", "DENIED"]
    reason: str
    
class WebhookResponse(BaseModel):
    status: str
    duplicate_event: bool = False
