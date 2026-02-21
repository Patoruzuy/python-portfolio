"""
Tests for CSP (Content Security Policy) manager.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.utils.csp_manager import CSPManager
from flask import Flask, g


class TestCSPManagerInit:
    """Test CSP manager initialization."""
    
    def test_init_without_app(self):
        """Should initialize without app."""
        csp = CSPManager()
        assert csp.app is None
        assert csp.violations == []


class TestNonceGeneration:
    """Test CSP nonce generation."""
    
    def test_nonce_is_url_safe(self):
        """Should generate URL-safe nonce."""
        app = Flask(__name__)
        csp = CSPManager(app)
        
        with app.test_request_context('/'):
            app.preprocess_request()
            nonce = g.csp_nonce
            
            # Should only contain URL-safe characters
            import re
            assert re.match(r'^[A-Za-z0-9_-]+$', nonce)
    
    def test_nonce_has_sufficient_length(self):
        """Should generate nonce with sufficient length."""
        app = Flask(__name__)
        csp = CSPManager(app)
        
        with app.test_request_context('/'):
            app.preprocess_request()
            nonce = g.csp_nonce
            
            # Should be reasonably long for security
            assert len(nonce) >= 16


class TestCSPPolicyBuilding:
    """Test CSP policy building."""
    
    def test_builds_basic_policy(self):
        """Should build basic CSP policy."""
        app = Flask(__name__)
        app.config['TESTING'] = False
        app.config['DEBUG'] = False
        csp = CSPManager(app)
        
        with app.test_request_context('/'):
            app.preprocess_request()
            nonce = g.csp_nonce
            policy = csp.build_policy(nonce)
            
            assert isinstance(policy, str)
            assert len(policy) > 0
    
    def test_includes_nonce_in_policy(self):
        """Should include nonce in script-src and style-src."""
        app = Flask(__name__)
        app.config['TESTING'] = False
        app.config['DEBUG'] = False
        csp = CSPManager(app)
        
        with app.test_request_context('/'):
            app.preprocess_request()
            nonce = g.csp_nonce
            policy = csp.build_policy(nonce)
            
            assert f"'nonce-{nonce}'" in policy
    
    def test_includes_script_src_directive(self):
        """Should include script-src directive."""
        app = Flask(__name__)
        app.config['TESTING'] = False
        app.config['DEBUG'] = False
        csp = CSPManager(app)
        
        policy = csp.build_policy('test_nonce')
        assert 'script-src' in policy
    
    def test_includes_style_src_directive(self):
        """Should include style-src directive."""
        app = Flask(__name__)
        app.config['TESTING'] = False
        app.config['DEBUG'] = False
        csp = CSPManager(app)
        
        policy = csp.build_policy('test_nonce')
        assert 'style-src' in policy
    
    def test_allows_self_by_default(self):
        """Should allow 'self' by default."""
        app = Flask(__name__)
        app.config['TESTING'] = False
        app.config['DEBUG'] = False
        csp = CSPManager(app)
        
        policy = csp.build_policy('test_nonce')
        assert "'self'" in policy


class TestCSPViolationReporting:
    """Test CSP violation reporting."""
    
    def test_logs_violation(self):
        """Should log CSP violations."""
        app = Flask(__name__)
        csp = CSPManager()  # Don't initialize with app - just test violation list
        
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            violation = {
                'csp-report': {
                    'document-uri': 'https://example.com/page',
                    'violated-directive': 'script-src',
                    'blocked-uri': 'https://evil.com/script.js'
                }
            }
            
            csp.log_violation(violation)
            
            assert len(csp.violations) > 0
            assert csp.violations[-1]['violation'] == violation


class TestGetViolations:
    """Test retrieving logged violations."""
    
    def test_returns_all_violations(self):
        """Should return all logged violations."""
        app = Flask(__name__)
        csp = CSPManager()  # Don't initialize with app
        
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            # Log some violations
            violation1 = {'csp-report': {'violated-directive': 'script-src'}}
            violation2 = {'csp-report': {'violated-directive': 'style-src'}}
            
            csp.log_violation(violation1)
            csp.log_violation(violation2)
            
            violations = csp.get_violations()
            
            assert len(violations) >= 2
    
    def test_returns_empty_list_initially(self):
        """Should return empty list when no violations."""
        csp = CSPManager()  # Don't initialize with app
        violations = csp.get_violations()
        
        assert isinstance(violations, list)
        assert len(violations) == 0


class TestClearViolations:
    """Test clearing violation log."""
    
    def test_clears_all_violations(self):
        """Should clear all logged violations."""
        app = Flask(__name__)
        csp = CSPManager()  # Don't initialize with app
        
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            # Log violations
            csp.log_violation({'csp-report': {'violated-directive': 'script-src'}})
            csp.log_violation({'csp-report': {'violated-directive': 'style-src'}})
            
            assert len(csp.violations) >= 2
            
            # Clear violations
            csp.clear_violations()
            
            assert len(csp.violations) == 0
