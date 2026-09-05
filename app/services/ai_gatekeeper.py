from app.schemas.events import NormalizedPaymentEvent, AIDecision
from app.llm import get_llm_provider
from app.config import settings

class AIGatekeeper:
    def __init__(self):
        self.provider = get_llm_provider()

    def classify(self, event: NormalizedPaymentEvent) -> AIDecision:
        """
        Classifies the incoming normalized event using the configured LLM provider.
        """
        decision = self.provider.classify_failure(event)
        return decision

    def get_provider_info(self) -> str:
        """
        Returns info about the active provider for the dashboard.
        """
        return settings.llm_provider.capitalize()
