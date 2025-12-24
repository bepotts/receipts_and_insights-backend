"""
Application configuration
"""
import os
from typing import Optional

# Note: Install python-dotenv to use: pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, continue without it
    pass


class Settings:
    """Application settings"""

    # Application
    APP_NAME: str = os.getenv("APP_NAME", "receipts_and_insights")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")

    # Database
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # API
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()

