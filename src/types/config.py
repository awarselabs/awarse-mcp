from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-pro"
    
    healwright_port: int = Field(
        8000, 
        validation_alias=AliasChoices("healwright_port", "awarse_port")
    )
    healwright_host: str = Field(
        "0.0.0.0", 
        validation_alias=AliasChoices("healwright_host", "awarse_host")
    )
    healwright_mock_heal: bool = Field(
        False, 
        validation_alias=AliasChoices("healwright_mock_heal", "awarse_mock_heal")
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
