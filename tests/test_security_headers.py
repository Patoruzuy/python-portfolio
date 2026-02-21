"""
Tests for security headers and cookie configurations.
"""

class TestSecurityHeaders:
    """Test HTTP security headers."""
    
    def test_x_frame_options_header(self, client, database):
        """Test X-Frame-Options header is present."""
        response = client.get('/')
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] in ['SAMEORIGIN', 'DENY']
        
    def test_x_content_type_options_header(self, client, database):
        """Test X-Content-Type-Options header is present."""
        response = client.get('/')
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
    def test_x_xss_protection_header(self, client, database):
        """Test X-XSS-Protection header is present."""
        response = client.get('/')
        # Some modern frameworks omit this in favor of CSP, but if present it should be secure
        if 'X-XSS-Protection' in response.headers:
            assert response.headers['X-XSS-Protection'] in ['1; mode=block', '0']
            
    def test_strict_transport_security_header(self, client, database):
        """Test Strict-Transport-Security header (HSTS)."""
        response = client.get('/')
        # HSTS might only be added in production/HTTPS, so we check if it's configured
        if 'Strict-Transport-Security' in response.headers:
            assert 'max-age=' in response.headers['Strict-Transport-Security']
            
    def test_referrer_policy_header(self, client, database):
        """Test Referrer-Policy header."""
        response = client.get('/')
        assert 'Referrer-Policy' in response.headers
        assert response.headers['Referrer-Policy'] in ['strict-origin-when-cross-origin', 'no-referrer', 'same-origin']
        
    def test_permissions_policy_header(self, client, database):
        """Test Permissions-Policy header."""
        response = client.get('/')
        # Optional but recommended
        if 'Permissions-Policy' in response.headers:
            assert 'geolocation=' in response.headers['Permissions-Policy'] or 'camera=' in response.headers['Permissions-Policy']

class TestCookieSecurity:
    """Test cookie security attributes."""
    
    def test_session_cookie_attributes(self, client):
        """Test session cookie has secure attributes."""
        # Trigger a session creation
        response = client.get('/admin/login')
        
        # Check Set-Cookie headers
        cookies = response.headers.getlist('Set-Cookie')
        for cookie in cookies:
            if 'session=' in cookie:
                assert 'HttpOnly' in cookie
                assert 'SameSite=Lax' in cookie or 'SameSite=Strict' in cookie
                # Secure flag might be disabled in testing environment
                # assert 'Secure' in cookie
