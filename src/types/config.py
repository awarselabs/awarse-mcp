from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-pro"
    awarse_port: int = 8000
    awarse_host: str = "0.0.0.0"
    awarse_mock_heal: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
