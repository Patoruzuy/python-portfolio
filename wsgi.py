"""
WSGI entry point for the portfolio application.

Usage:
    Development : python wsgi.py
    Production  : waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
    Gunicorn    : gunicorn wsgi:app
"""
from app import app  # noqa: F401

if __name__ == "__main__":
    import os
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
