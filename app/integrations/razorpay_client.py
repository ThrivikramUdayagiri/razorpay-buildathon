import razorpay
from app.config import settings
import logging

class RazorpayClient:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )
        self.client.set_app_details({"title": "Revox", "version": "1.0"})

    def verify_webhook_signature(self, payload_body: str, signature: str) -> bool:
        try:
            self.client.utility.verify_webhook_signature(
                payload_body,
                signature,
                settings.razorpay_webhook_secret
            )
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    def create_order(self, amount: float, currency: str = "INR", receipt: str = None) -> dict:
        try:
            return self.client.order.create({
                "amount": int(amount * 100), # Razorpay expects paise
                "currency": currency,
                "receipt": receipt,
                "payment_capture": 1
            })
        except Exception as e:
            logging.error(f"Error creating order: {e}")
            return None

    def create_payment_link(self, amount: float, currency: str = "INR", description: str = None, customer: dict = None) -> dict:
        try:
            return self.client.payment_link.create({
                "amount": int(amount * 100),
                "currency": currency,
                "description": description,
                "customer": customer or {}
            })
        except Exception as e:
            logging.error(f"Error creating payment link: {e}")
            return None
