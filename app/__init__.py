"""
Application package.

Re-exports the Flask application instance and key extensions so that
external code (tests, scripts, Celery tasks) can continue to use:

    from app import app, db, cache, mail
"""
from app.app import app, db, cache, mail  # noqa: F401

__all__ = ["app", "db", "cache", "mail"]
