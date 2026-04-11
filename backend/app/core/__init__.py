"""
Core module initialization.
Expose configuration, logging, and custom exceptions in one place.
"""

from .config import Settings, get_settings
from . import logging as logging
from . import exceptions as exceptions
from .exceptions import TutorRAGErrors, DocumentError, RetrievalError

settings = get_settings()
logger = logging.logger
log = logger


def get_app_settings() -> Settings:
    """Return the cached application settings."""
    return settings


__all__ = [
    "Settings",
    "get_settings",
    "get_app_settings",
    "settings",
    "logging",
    "logger",
    "log",
    "exceptions",
    "TutorRAGErrors",
    "DocumentError",
    "RetrievalError",
]