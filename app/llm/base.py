from abc import ABC, abstractmethod
from app.schemas.events import NormalizedPaymentEvent, AIDecision

class LLMProvider(ABC):
    @abstractmethod
    def classify_failure(self, event: NormalizedPaymentEvent) -> AIDecision:
        """
        Analyzes the failure event and returns a structured AI decision.
        """
        pass
