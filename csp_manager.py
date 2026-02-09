"""
Content Security Policy (CSP) Implementation
Provides nonce-based CSP headers and violation reporting.
"""

import secrets
from flask import request, jsonify, g
from datetime import datetime
import json


class CSPManager:
    """
    Manages Content Security Policy with nonce generation and violation reporting.
    
    Features:
    - Generates unique nonces per request
    - Configurable CSP directives
    - CSP violation logging endpoint
    """
    
    def __init__(self, app=None):
        self.app = app
        self.violations = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize CSP with Flask app."""
        self.app = app
        
        # Generate nonce before each request
        @app.before_request
        def generate_nonce():
            g.csp_nonce = secrets.token_urlsafe(16)
        
        # Add CSP headers after each request
        @app.after_request
        def add_csp_headers(response):
            if request.endpoint and not request.endpoint.startswith('static'):
                nonce = getattr(g, 'csp_nonce', None)
                
                # Build CSP policy
                policy = self.build_policy(nonce)
                
                # Add CSP header
                response.headers['Content-Security-Policy'] = policy
                
                # Add additional security headers
                response.headers['X-Content-Type-Options'] = 'nosniff'
                response.headers['X-Frame-Options'] = 'SAMEORIGIN'
                response.headers['X-XSS-Protection'] = '1; mode=block'
                response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
                
            return response
        
        # Add CSP violation reporting endpoint
        @app.route('/csp-report', methods=['POST'])
        def csp_report():
            """Endpoint for receiving CSP violation reports."""
            try:
                violation = request.get_json(force=True)
                
                # Log violation
                self.log_violation(violation)
                
                return jsonify({'status': 'ok'}), 204
            except Exception as e:
                app.logger.error(f"CSP report error: {e}")
                return jsonify({'status': 'error'}), 400
        
        # Make nonce available to templates
        @app.context_processor
        def inject_csp_nonce():
            return {
                'csp_nonce': lambda: getattr(g, 'csp_nonce', '')
            }
    
    def build_policy(self, nonce=None):
        """
        Build CSP policy string.
        
        Args:
            nonce: Unique nonce for this request
            
        Returns:
            CSP policy string
        """
        directives = []
        
        # Default source: only same origin
        directives.append("default-src 'self'")
        
        # Scripts: self + nonce for inline scripts
        if nonce:
            directives.append(f"script-src 'self' 'nonce-{nonce}'")
        else:
            directives.append("script-src 'self'")
        
        # Styles: self + nonce for inline styles
        if nonce:
            directives.append(f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline'")
        else:
            directives.append("style-src 'self' 'unsafe-inline'")
        
        # Images: self + data URIs (for inline images)
        directives.append("img-src 'self' data: https:")
        
        # Fonts: self
        directives.append("font-src 'self'")
        
        # Connect: self (for AJAX)
        directives.append("connect-src 'self'")
        
        # Frame ancestors: none (prevent clickjacking)
        directives.append("frame-ancestors 'none'")
        
        # Base URI: self
        directives.append("base-uri 'self'")
        
        # Form action: self
        directives.append("form-action 'self'")
        
        # Report violations
        if self.app and not self.app.debug:
            directives.append("report-uri /csp-report")
        
        return '; '.join(directives)
    
    def log_violation(self, violation):
        """
        Log a CSP violation.
        
        Args:
            violation: Violation report dict from browser
        """
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'violation': violation,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
            'ip': request.remote_addr
        }
        
        self.violations.append(entry)
        
        # Log to Flask logger
        if self.app:
            self.app.logger.warning(f"CSP Violation: {json.dumps(violation, indent=2)}")
        
        # Keep only last 100 violations in memory
        if len(self.violations) > 100:
            self.violations = self.violations[-100:]
    
    def get_violations(self, limit=50):
        """Get recent CSP violations."""
        return self.violations[-limit:]
    
    def clear_violations(self):
        """Clear all logged violations."""
        self.violations.clear()


# Global instance
_csp_manager = None


def init_csp(app):
    """
    Initialize CSP manager with Flask app.
    
    Args:
        app: Flask application instance
        
    Returns:
        CSPManager instance
    """
    global _csp_manager
    _csp_manager = CSPManager(app)
    return _csp_manager


def get_csp_manager():
    """Get the global CSPManager instance."""
    return _csp_manager


# Development helper
def disable_csp(app):
    """
    Disable CSP for development/testing.
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def remove_csp(response):
        response.headers.pop('Content-Security-Policy', None)
        return response
