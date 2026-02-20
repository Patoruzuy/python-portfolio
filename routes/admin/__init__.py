"""
Admin sub-blueprints coordinator.

Registers all admin blueprints:
- auth: Login, logout, password reset, security
- dashboard: Main dashboard and analytics
- blog: Blog post management
- newsletter: Newsletter subscriber management
- projects: Projects and Raspberry Pi management
- products: Product management
- settings: Site configuration and owner profile
- media: Image uploads
"""
from flask import Flask
from routes.admin.auth import admin_auth_bp
from routes.admin.dashboard import admin_dashboard_bp
from routes.admin.blog import admin_blog_bp
from routes.admin.newsletter import admin_newsletter_bp
from routes.admin.projects import admin_projects_bp
from routes.admin.products import admin_products_bp
from routes.admin.settings import admin_settings_bp
from routes.admin.media import admin_media_bp


def register_admin_blueprints(app: Flask) -> None:
    """Register all admin sub-blueprints."""
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_blog_bp)
    app.register_blueprint(admin_newsletter_bp)
    app.register_blueprint(admin_projects_bp)
    app.register_blueprint(admin_products_bp)
    app.register_blueprint(admin_settings_bp)
    app.register_blueprint(admin_media_bp)
