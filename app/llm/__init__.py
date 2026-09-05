from .base import LLMProvider
from .mock import MockProvider
from .gemini import GeminiProvider
from app.config import settings

def get_llm_provider() -> LLMProvider:
    provider_name = settings.llm_provider.lower()
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name == "openai":
        # We can implement OpenAIProvider later if needed, fallback to mock for now
        return MockProvider()
    else:
        return MockProvider()
