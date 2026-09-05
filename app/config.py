from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    razorpay_key_id: str = "rzp_test_placeholder"
    razorpay_key_secret: str = "placeholder_secret"
    razorpay_webhook_secret: str = "placeholder_webhook_secret"
    razorpay_mode: Literal["simulation", "test"] = "simulation"

    llm_provider: Literal["mock", "gemini", "openai"] = "mock"
    llm_api_key: str = ""

    database_url: str = "sqlite:///./revox.db"
    debug: bool = True
    max_recovery_touchpoints: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
