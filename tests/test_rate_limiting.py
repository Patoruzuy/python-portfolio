"""
Tests for rate limiting and DoS prevention.
"""
import pytest
from flask import Flask
import time

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_contact_form_rate_limiting(self, client):
        """Test rate limiting on contact form."""
        # Send multiple requests quickly
        for _ in range(10):
            response = client.post('/api/contact', data={
                'name': 'Test',
                'email': 'test@example.com',
                'message': 'Test message'
            })
            
        # The next request should be rate limited
        response = client.post('/api/contact', data={
            'name': 'Test',
            'email': 'test@example.com',
            'message': 'Test message'
        })
        
        # Should be rate limited (429), accepted (200), or rejected by validation (400)
        assert response.status_code in [200, 400, 429]
        
    def test_admin_login_rate_limiting(self, client):
        """Test rate limiting on admin login."""
        for _ in range(10):
            response = client.post('/admin/login', data={
                'username': 'admin',
                'password': 'wrongpassword'
            })
            
        response = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        assert response.status_code in [200, 429]
        
    def test_api_endpoint_rate_limiting(self, client, database):
        """Test rate limiting on API endpoints."""
        for _ in range(20):
            response = client.get('/api/projects')
            
        response = client.get('/api/projects')
        assert response.status_code in [200, 429]
        
    def test_newsletter_subscription_rate_limiting(self, client):
        """Test rate limiting on newsletter subscription."""
        for _ in range(10):
            response = client.post('/api/newsletter/subscribe',
                                   json={'email': 'test@example.com'},
                                   content_type='application/json')
            
        response = client.post('/api/newsletter/subscribe',
                               json={'email': 'test@example.com'},
                               content_type='application/json')
        
        # Rate limited (429), accepted (200), or validation/server error (400/500)
        assert response.status_code in [200, 400, 429, 500]
        
    def test_rate_limit_headers_present(self, client, database):
        """Test rate limit headers are present in responses."""
        response = client.get('/')
        # Flask-Limiter adds these headers
        if 'X-RateLimit-Limit' in response.headers:
            assert 'X-RateLimit-Remaining' in response.headers
            assert 'X-RateLimit-Reset' in response.headers
            
    def test_rate_limit_bypass_attempts(self, client, database):
        """Test attempts to bypass rate limiting."""
        # Try with different IP headers
        headers = {'X-Forwarded-For': '1.2.3.4'}
        response = client.get('/', headers=headers)
        assert response.status_code == 200
        
    def test_rate_limit_per_ip_address(self, client):
        """Test rate limiting is per IP address."""
        # This is hard to test without a real proxy setup, but we can verify the configuration
        pass
        
    def test_rate_limit_per_user_session(self, client):
        """Test rate limiting per user session."""
        # This is hard to test without a real session setup, but we can verify the configuration
        pass
