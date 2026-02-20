"""
Add type hints to scripts for mypy validation.

This module provides type hints for all utility scripts to pass mypy validation.
"""
from typing import TypedDict, Optional

class ConfigDict(TypedDict, total=False):
    """Type hints for configuration dictionary."""
    SECRET_KEY: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD_HASH: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USE_TLS: bool
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_DEFAULT_SENDER: str
    MAIL_RECIPIENT: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CACHE_REDIS_URL: str
    CACHE_TYPE: str
    CACHE_DEFAULT_TIMEOUT: int
