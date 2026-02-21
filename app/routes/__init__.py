"""
Routes package initialization.
"""
from flask import Flask


def register_all_blueprints(app: Flask) -> None:
    """Register all route blueprints with the Flask application."""
    from app.routes.public import public_bp
    from app.routes.api import (
        api_bp,
        register_api_csrf_exemptions,
        register_public_newsletter_routes,
    )
    from app.routes.analytics import analytics_bp
    from app.routes.gdpr import gdpr_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    register_api_csrf_exemptions(app)
    register_public_newsletter_routes(app)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(gdpr_bp)
