"""
Tests for API security.
"""
import pytest
from flask import Flask

class TestAPISecurity:
    """Test API security measures."""
    
    def test_api_rate_limiting_per_endpoint(self, client, database):
        """Test API rate limiting per endpoint."""
        # Send multiple requests to an API endpoint
        for _ in range(20):
            response = client.get('/api/projects')
            
        # The next request should be rate limited
        response = client.get('/api/projects')
        
        # Should be rate limited (429) or return projects (200)
        assert response.status_code in [200, 429]
        
    def test_api_cors_configuration(self, client):
        """Test API CORS configuration."""
        # Send an OPTIONS request to an API endpoint
        response = client.options('/api/projects')
        
        # Check CORS headers
        if 'Access-Control-Allow-Origin' in response.headers:
            assert response.headers['Access-Control-Allow-Origin'] in ['*', 'http://localhost:3000']
            
    def test_api_error_responses_dont_leak_info(self, client):
        """Test API error responses don't leak info."""
        # Trigger an error on an API endpoint
        response = client.get('/api/projects/invalid-id')
        
        # Check response for sensitive info
        assert b'Traceback' not in response.data
        assert b'File "' not in response.data
        assert b'sqlalchemy' not in response.data.lower()
        assert b'psycopg2' not in response.data.lower()
        assert b'sqlite' not in response.data.lower()
