import os
import json
from google import genai
from pydantic import ValidationError
from .base import LLMProvider
from app.schemas.events import NormalizedPaymentEvent, AIDecision
from app.config import settings

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.llm_api_key
        # Only initialize if key is present to avoid crash on import
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def classify_failure(self, event: NormalizedPaymentEvent) -> AIDecision:
        if not self.client:
            # Fallback to safe default if not configured properly
            return AIDecision(intent="NO_ACTION", reason="UNKNOWN", recommended_action="NO_ACTION", confidence=0.0)

        prompt = f"""
        You are an AI Gatekeeper for a payment recovery system.
        Analyze the following failed payment event and determine the optimal recovery strategy to maximize payment success probability.
        
        Event Details:
        - Type: {event.event_type}
        - Occurred At: {event.occurred_at} (UTC)
        - Amount: {event.amount} {event.currency}
        - Subscription ID: {event.subscription_id}
        - Error Code: {event.failure_code}
        - Error Description: {event.failure_description}
        
        RULES FOR DYNAMIC SCHEDULING (delay_hours):
        - If the failure is due to 'bank timeout' or 'gateway error', calculate the `delay_hours` to schedule the retry during off-peak night hours (e.g., 2:00 AM - 4:00 AM local time) when bank server traffic is lowest.
        - If the failure is 'insufficient funds', recommend a delay (e.g., 24-72 hours) that aligns with typical salary deposit periods or beginning/middle of the month.
        
        Return a strict JSON object matching this schema:
        {{
            "intent": "RECOVER" | "DELAY" | "HARD_STOP" | "INVALIDATE" | "NO_ACTION",
            "reason": "INSUFFICIENT_FUNDS" | "BANK_TIMEOUT" | "MANDATE_REVOKED" | "PAYMENT_FAILED" | "CART_ABANDONED" | "ALREADY_PAID" | "STALE_CART" | "UNKNOWN",
            "recommended_action": "DELAY_RETRY" | "SCHEDULE_RECOVERY" | "GENERATE_PAYMENT_LINK" | "CREATE_RESUME_SESSION" | "INVALIDATE_RECOVERY" | "HARD_STOP" | "NO_ACTION",
            "delay_hours": <integer representing optimal hours to wait to maximize success>,
            "customer_contact_allowed": <boolean>,
            "confidence": <float between 0 and 1>
        }}
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            return AIDecision(**data)
        except Exception as e:
            print(f"Gemini AI Error: {e}")
            return AIDecision(intent="NO_ACTION", reason="UNKNOWN", recommended_action="NO_ACTION", confidence=0.0)
