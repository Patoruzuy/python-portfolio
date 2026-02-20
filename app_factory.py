"""
Application Factory for Flask App
Implements the Flask application factory pattern for better testing and modularity.
"""

from flask import Flask
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_caching import Cache
from typing import Optional
import sys
from sqlalchemy.exc import SQLAlchemyError

from config import get_config, DopplerConfig
from models import db
from celery_config import make_celery
from scripts.cache_buster import init_cache_buster
from utils.endpoint_url_fallbacks import install_endpoint_url_for_fallback
from utils.csp_manager import init_csp
from utils.rate_limiter import init_limiter, create_rate_limit_error_handler


def safe_console_log(message: str, fallback: Optional[str] = None) -> None:
    """Print startup/runtime messages without crashing on limited terminals."""
    try:
        print(message)
    except UnicodeEncodeError:
        if fallback:
            print(fallback)
            return
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        safe_message = message.encode(encoding, errors='replace').decode(encoding)
        print(safe_message)


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory to create and configure Flask app.
    
    Args:
        config_name: Configuration to use (e.g., 'development', 'production', 'testing')
                    If None, uses get_config() which auto-detects from environment
    
    Returns:
        Configured Flask application instance
    """
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name) if config_name else get_config()
    app.config.from_object(config_class)
    
    # Log configuration source
    if DopplerConfig.is_doppler_active():
        doppler_info = DopplerConfig.get_doppler_info()
        safe_console_log(
            f"🔐 Configuration loaded from Doppler: {doppler_info}",
            fallback=f"[INFO] Configuration loaded from Doppler: {doppler_info}"
        )
    else:
        safe_console_log(
            "📁 Configuration loaded from .env file",
            fallback="[INFO] Configuration loaded from .env file"
        )
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    install_endpoint_url_for_fallback(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register context processors
    register_context_processors(app)
    
    # Register Jinja filters
    register_jinja_filters(app)
    
    # Configure email from database
    with app.app_context():
        configure_email_from_db(app)
    
    return app


def initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions with the app."""
    # Database
    db.init_app(app)
    
    # CSRF Protection
    csrf = CSRFProtect(app)
    
    # Cache
    cache = Cache(app, config={
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'simple'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
        'CACHE_REDIS_URL': app.config.get('CACHE_REDIS_URL')
    })
    
    # Celery
    make_celery(app)
    
    # Cache Buster
    cache_buster = init_cache_buster(app)
    
    # CSP Manager
    csp = init_csp(app)
    
    # Rate Limiter
    limiter = init_limiter(app)
    rate_limit_handler = create_rate_limit_error_handler(limiter)
    app.register_error_handler(429, rate_limit_handler)
    
    safe_console_log(
        "🛡️  Rate limiting enabled with Redis storage",
        fallback="[INFO] Rate limiting enabled"
    )
    
    # Talisman (HTTPS security headers)
    if not app.config.get('TESTING'):
        Talisman(app, content_security_policy=None)
    
    # Mail
    mail = Mail(app)
    
    # Store references for later use
    app.extensions['csrf'] = csrf
    app.extensions['cache'] = cache
    app.extensions['cache_buster'] = cache_buster
    app.extensions['csp'] = csp
    app.extensions['limiter'] = limiter
    app.extensions['mail'] = mail


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints."""
    # Import blueprints (avoid circular imports)
    from routes import register_all_blueprints
    from routes.admin import register_admin_blueprints
    
    # Register public blueprints
    register_all_blueprints(app)
    
    # Register admin sub-blueprints
    register_admin_blueprints(app)


def register_error_handlers(app: Flask) -> None:
    """Register custom error handlers."""
    from flask import render_template
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        if app.config.get('DEBUG'):
            return render_template('500.html'), 500
        return render_template('404.html'), 404


def register_context_processors(app: Flask) -> None:
    """Register Jinja context processors."""
    from datetime import datetime, timezone
    from models import SiteConfig, OwnerProfile
    
    @app.context_processor
    def inject_site_data():
        """Inject site config and current year into all templates"""
        try:
            config = SiteConfig.query.first()
            owner = OwnerProfile.query.first()
        except SQLAlchemyError:
            db.session.rollback()
            config = None
            owner = None

        # Keep compatibility with templates that expect `owner` and always-available site config.
        if owner is None:
            owner = OwnerProfile(
                name="Portfolio Owner",
                title="Developer",
                email="contact@example.com",
            )
        if config is None:
            config = SiteConfig(
                site_name="Developer Portfolio",
                blog_enabled=True,
                products_enabled=True,
            )

        return {
            'site_config': config,
            'owner': owner,
            'owner_profile': owner,
            'current_year': datetime.now(timezone.utc).year,
            'now': datetime.now(timezone.utc)
        }


def register_jinja_filters(app: Flask) -> None:
    """Register custom Jinja filters."""
    @app.template_filter('format_date')
    def format_date_filter(value, format_str='%B %d, %Y'):
        """Format datetime object to readable string"""
        if value is None:
            return ''
        return value.strftime(format_str)
    
    @app.template_filter('format_datetime')
    def format_datetime_filter(value, format_str='%B %d, %Y at %I:%M %p'):
        """Format datetime object with time"""
        if value is None:
            return ''
        return value.strftime(format_str)

    @app.template_filter('slugify')
    def slugify_filter(value: object) -> str:
        """Generate URL-safe slugs in templates."""
        if value is None:
            return ''

        text = str(value)
        try:
            from slugify import slugify as python_slugify
            return python_slugify(text)
        except ImportError:
            # Lightweight fallback keeps templates functional if dependency is unavailable.
            import re
            return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def configure_email_from_db(app: Flask) -> None:
    """Load email configuration from database SiteConfig."""
    from models import SiteConfig
    
    try:
        config = SiteConfig.query.first()
        if config and config.mail_server:
            app.config['MAIL_SERVER'] = config.mail_server
            app.config['MAIL_PORT'] = config.mail_port
            app.config['MAIL_USE_TLS'] = config.mail_use_tls
            app.config['MAIL_USERNAME'] = config.mail_username
            app.config['MAIL_DEFAULT_SENDER'] = config.mail_default_sender
            safe_console_log(
                "📧 Email configuration loaded from database",
                fallback="[INFO] Email config loaded from DB"
            )
    except Exception as e:
        safe_console_log(
            f"⚠️  Could not load email config from database: {e}",
            fallback=f"[WARN] Email config error: {e}"
        )


# Create default app instance for backward compatibility
app = create_app()
