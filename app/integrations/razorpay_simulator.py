import hashlib
import hmac
from app.config import settings

class RazorpaySimulator:
    """
    Deterministic simulator for the demo mode. 
    Does not make any network calls.
    """
    
    def verify_webhook_signature(self, payload_body: str, signature: str) -> bool:
        # Re-implement the standard HMAC verification for offline testing
        expected_signature = hmac.new(
            settings.razorpay_webhook_secret.encode('utf-8'),
            payload_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

    def create_order(self, amount: float, currency: str = "INR", receipt: str = None) -> dict:
        return {
            "id": "order_sim_" + hashlib.md5(str(amount).encode()).hexdigest()[:10],
            "entity": "order",
            "amount": int(amount * 100),
            "currency": currency,
            "receipt": receipt,
            "status": "created",
            "simulated": True
        }

    def create_payment_link(self, amount: float, currency: str = "INR", description: str = None, customer: dict = None) -> dict:
        return {
            "id": "plink_sim_" + hashlib.md5(str(amount).encode()).hexdigest()[:10],
            "entity": "payment_link",
            "short_url": "https://sim.razorpay.com/plink_sim",
            "amount": int(amount * 100),
            "currency": currency,
            "status": "created",
            "simulated": True
        }
