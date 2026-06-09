"""
config.py - Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "LeadPilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./leadpilot.db"

    # Groq LLM
    GROQ_API_KEY: Optional[str] = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_HEAVY_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_LIGHT_MODEL: str = "llama-3.1-8b-instant"

    # SMTP Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_EMAIL: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Report paths
    REPORTS_DIR: str = "reports"

    @property
    def has_groq_key(self) -> bool:
        """Check if Groq API key is configured."""
        return bool(self.GROQ_API_KEY and self.GROQ_API_KEY.strip())

    @property
    def has_smtp_config(self) -> bool:
        """Check if SMTP is fully configured."""
        return all([
            self.SMTP_HOST,
            self.SMTP_EMAIL,
            self.SMTP_PASSWORD,
        ])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
