"""
Configuration module for IBCo Vallejo Console.

Provides centralized configuration management and logging setup.
All application settings are loaded from environment variables via Pydantic Settings.
"""

from src.config.settings import settings
from src.config.logging_config import get_logger, setup_logging

__all__ = ["settings", "get_logger", "setup_logging"]
