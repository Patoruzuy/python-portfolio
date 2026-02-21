"""
Rate limiting configuration for Flask application.
Protects against brute force attacks, spam, and abuse.
"""

from typing import Optional, Callable, Dict, Any
from flask import Flask, request, Request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib


def get_request_identifier() -> str:
    """
    Get unique identifier for rate limiting.
    Uses IP address, or X-Forwarded-For if behind proxy.
    
    Returns:
        str: IP address or client identifier
    """
    # Check if behind proxy
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Get first IP in chain (client IP)
        return forwarded_for.split(',')[0].strip()
    return get_remote_address()


def get_api_key_identifier() -> str:
    """
    Get identifier for API key-based rate limiting.
    Falls back to IP if no API key present.
    
    Returns:
        str: Hashed API key or IP address
    """
    api_key: Optional[str] = request.headers.get('X-API-Key')
    if api_key:
        # Hash API key for privacy
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    return get_request_identifier()


# Rate limiting strategies
RATE_LIMITS: Dict[str, str] = {
    # Authentication endpoints - stricter limits
    'auth_strict': '5 per hour',      # Login attempts
    'auth_normal': '10 per hour',     # Password reset requests
    
    # API endpoints - moderate limits
    'api_contact': '5 per hour',      # Contact form submissions
    'api_newsletter': '3 per day',    # Newsletter subscriptions
    'api_normal': '100 per hour',     # General API calls
    
    # Public pages - generous limits
    'page_view': '500 per hour',      # Regular page views
    
    # Admin operations - moderate limits
    'admin_write': '60 per hour',     # Content creation/updates
    'admin_read': '300 per hour',     # Admin dashboard access
}


def init_limiter(app: Flask) -> Limiter:
    """
    Initialize rate limiter with Flask app.
    
    Args:
        app: Flask application instance
        
    Returns:
        Limiter: Configured rate limiter instance
    """
    # Get Redis URL from config
    storage_uri: str = app.config.get('REDIS_URL', 'redis://localhost:6379/1')
    
    limiter = Limiter(
        app=app,
        key_func=get_request_identifier,
        storage_uri=storage_uri,
        storage_options={
            'socket_connect_timeout': 30,
            'socket_timeout': 30,
        },
        strategy='fixed-window',
        default_limits=['1000 per hour'],  # Global default
        headers_enabled=True,  # Send rate limit info in response headers
        swallow_errors=True,   # Don't crash if Redis unavailable
    )
    
    return limiter


def create_rate_limit_error_handler(limiter: Limiter) -> Callable:
    """
    Create custom error handler for rate limit exceeded.
    
    Args:
        limiter: Limiter instance
        
    Returns:
        Callable: Error handler function
    """
    @limiter.request_filter
    def whitelist_admin() -> bool:
        """Skip rate limiting for admin endpoints in development."""
        import os
        if os.getenv('FLASK_ENV') == 'development':
            return request.path.startswith('/admin/')
        return False
    
    def rate_limit_handler(e: Exception) -> tuple:
        """Handle rate limit exceeded errors."""
        from flask import jsonify
        
        # API endpoints return JSON
        if request.path.startswith('/api/'):
            error_desc = str(getattr(e, 'description', 'Rate limit exceeded'))
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': error_desc,
                'retry_after': error_desc.split('in ')[1] if 'in ' in error_desc else 'unknown'
            }), 429
        
        # Web pages return HTML error
        from flask import render_template
        return render_template(
            '429.html',
            retry_after=str(getattr(e, 'description', 'Rate limit exceeded'))
        ), 429
    
    return rate_limit_handler
