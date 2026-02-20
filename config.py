"""
Configuration module for Flask application.
Supports loading from .env file and Doppler secrets management.

Environment Variables Priority:
1. Doppler (if configured)
2. System environment variables
3. .env file
4. Default values
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file if it exists (Doppler will override if configured)
load_dotenv()


def env_bool(name, default=False):
    """Parse environment booleans with common truthy values."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


class Config:
    """Base configuration class with sensible defaults."""
    
    # Flask Core Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    TESTING = env_bool('FLASK_TESTING', False)
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///portfolio.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery Configuration (async tasks)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Site Configuration
    SITE_URL = os.getenv('SITE_URL', 'http://localhost:5000')
    
    # Email Configuration (Flask-Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    MAIL_RECIPIENT = os.getenv('MAIL_RECIPIENT', os.getenv('MAIL_USERNAME'))
    CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', os.getenv('MAIL_USERNAME'))
    
    # Admin Configuration
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    # SECURITY: No default password hash - must be set in environment
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')
    if not ADMIN_PASSWORD_HASH:
        import sys
        print("⚠️  WARNING: ADMIN_PASSWORD_HASH not set in environment!")
        print("   Admin login will not work until password is configured.")
        print("   Generate hash with: python -c 'from werkzeug.security import generate_password_hash; print(generate_password_hash(\"your_password\"))'")
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    
    # Session Configuration
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.getenv('SESSION_LIFETIME_DAYS', 7)))
    
    # Remember Me Cookie Configuration
    REMEMBER_COOKIE_SECURE = os.getenv('REMEMBER_COOKIE_SECURE', 'True').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = os.getenv('REMEMBER_COOKIE_HTTPONLY', 'True').lower() == 'true'
    REMEMBER_COOKIE_DURATION = timedelta(days=int(os.getenv('REMEMBER_COOKIE_DAYS', 30)))
    
    # Cache Configuration
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    CACHE_REDIS_URL = os.getenv('CACHE_REDIS_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    
    # Rate Limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100/hour')
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/images')
    UPLOAD_URL_PREFIX = os.getenv('UPLOAD_URL_PREFIX', '')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    
    # Blog Configuration
    BLOG_POSTS_DIR = os.getenv('BLOG_POSTS_DIR', 'blog_posts')
    POSTS_PER_PAGE = int(os.getenv('POSTS_PER_PAGE', 10))
    
    # Analytics Configuration
    GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID')
    ENABLE_SELF_HOSTED_ANALYTICS = os.getenv('ENABLE_SELF_HOSTED_ANALYTICS', 'True').lower() == 'true'
    ANALYTICS_RETENTION_DAYS = int(os.getenv('ANALYTICS_RETENTION_DAYS', 90))
    
    # Security Headers
    HSTS_MAX_AGE = int(os.getenv('HSTS_MAX_AGE', 31536000))  # 1 year
    HSTS_INCLUDE_SUBDOMAINS = os.getenv('HSTS_INCLUDE_SUBDOMAINS', 'True').lower() == 'true'
    HSTS_PRELOAD = os.getenv('HSTS_PRELOAD', 'False').lower() == 'true'
    
    # Error Tracking (Sentry)
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', os.getenv('FLASK_ENV', 'production'))
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.1))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    
    # Feature Flags
    ENABLE_NEWSLETTER = os.getenv('ENABLE_NEWSLETTER', 'True').lower() == 'true'
    ENABLE_CONTACT_FORM = os.getenv('ENABLE_CONTACT_FORM', 'True').lower() == 'true'
    ENABLE_BLOG_COMMENTS = os.getenv('ENABLE_BLOG_COMMENTS', 'False').lower() == 'true'
    ENABLE_ECOMMERCE = os.getenv('ENABLE_ECOMMERCE', 'False').lower() == 'true'
    
    # Gunicorn Configuration (for deployment)
    WORKERS = int(os.getenv('WORKERS', 4))
    WORKER_CLASS = os.getenv('WORKER_CLASS', 'sync')
    BIND = os.getenv('BIND', '0.0.0.0:5000')
    TIMEOUT = int(os.getenv('TIMEOUT', 120))
    GRACEFUL_TIMEOUT = int(os.getenv('GRACEFUL_TIMEOUT', 30))
    KEEPALIVE = int(os.getenv('KEEPALIVE', 5))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        pass
    
    @classmethod
    def get_all_config(cls):
        """Get all configuration as a dictionary (excluding sensitive data)."""
        sensitive_keys = {
            'SECRET_KEY',
            'MAIL_PASSWORD',
            'ADMIN_PASSWORD_HASH',
            'SENTRY_DSN',
            'DATABASE_URL',
            'SQLALCHEMY_DATABASE_URI',
            'REDIS_URL',
            'CELERY_BROKER_URL',
            'CELERY_RESULT_BACKEND',
            'CACHE_REDIS_URL',
            'RATELIMIT_STORAGE_URL',
        }
        
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') 
            and not callable(value)
            and key not in sensitive_keys
        }
    
    @classmethod
    def validate_required_config(cls):
        """
        Validate that required configuration is present.
        Returns tuple (is_valid, missing_keys)
        """
        required_keys = ['SECRET_KEY', 'MAIL_USERNAME']
        missing = []
        
        for key in required_keys:
            value = getattr(cls, key, None)
            if not value or value.startswith('dev-') or value == 'your-':
                missing.append(key)
        
        return len(missing) == 0, missing


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    HSTS_PRELOAD = False


class ProductionConfig(Config):
    """Production configuration with enhanced security."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    HSTS_INCLUDE_SUBDOMAINS = True
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization."""
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        
        handler = StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


class DopplerConfig(Config):
    """
    Doppler-specific configuration.
    
    When using Doppler CLI (doppler run -- python app.py),
    all environment variables are automatically injected.
    This class ensures proper handling of Doppler secrets.
    """
    
    @classmethod
    def is_doppler_active(cls):
        """Check if running under Doppler."""
        return os.getenv('DOPPLER_ENVIRONMENT') is not None or os.getenv('DOPPLER_PROJECT') is not None
    
    @classmethod
    def get_doppler_info(cls):
        """Get Doppler configuration information."""
        if not cls.is_doppler_active():
            return None
        
        return {
            'project': os.getenv('DOPPLER_PROJECT'),
            'config': os.getenv('DOPPLER_CONFIG'),
            'environment': os.getenv('DOPPLER_ENVIRONMENT'),
        }


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'doppler': DopplerConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """
    Get configuration class based on environment.
    
    Args:
        env: Environment name ('development', 'production', 'testing', 'doppler')
             If None, uses FLASK_ENV environment variable.
    
    Returns:
        Configuration class
    """
    if env is None:
        # Check if Doppler is active
        if DopplerConfig.is_doppler_active():
            env = 'doppler'
        elif env_bool('FLASK_TESTING', False):
            env = 'testing'
        else:
            env = os.getenv('FLASK_ENV', 'development')
    
    return config.get(env, config['default'])
