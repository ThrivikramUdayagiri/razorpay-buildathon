from .razorpay_client import RazorpayClient
from .razorpay_simulator import RazorpaySimulator
from app.config import settings

def get_razorpay_adapter():
    if settings.razorpay_mode == "test":
        return RazorpayClient()
    return RazorpaySimulator()
