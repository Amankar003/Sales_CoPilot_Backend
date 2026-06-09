"""
settings.py - Global settings instance.
Import this wherever you need access to configuration.
"""

from app.core.config import Settings

# Global settings instance - created once, used everywhere
settings = Settings()
