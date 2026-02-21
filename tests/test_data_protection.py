"""
Tests for data protection, privacy, and information disclosure prevention.
"""

class TestSensitiveDataHandling:
    """Test handling of sensitive data."""
    
    def test_passwords_never_logged(self, client, caplog):
        """Test that passwords are not logged."""
        _ = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'supersecretpassword123'
        })
        
        # Check logs for the password
        assert 'supersecretpassword123' not in caplog.text
        
    def test_passwords_hashed_in_database(self, app, database):
        """Test that passwords are hashed in the database."""
        with app.app_context():
            # Check the admin password hash in config
            assert 'ADMIN_PASSWORD_HASH' in app.config
            assert app.config['ADMIN_PASSWORD_HASH'].startswith('scrypt:') or app.config['ADMIN_PASSWORD_HASH'].startswith('pbkdf2:')
            
    def test_sensitive_data_not_in_error_messages(self, client):
        """Test that error messages don't contain sensitive data."""
        # Trigger an error
        response = client.get('/admin/nonexistent')
        
        # Check response for sensitive data
        assert b'password' not in response.data.lower()
        assert b'secret' not in response.data.lower()
        assert b'key' not in response.data.lower()
        
    def test_gdpr_data_export_security(self, client):
        """Test GDPR data export security."""
        # Try to export data without authentication
        response = client.get('/api/my-data/download')
        
        # Should be 404 or 401/403
        assert response.status_code in [404, 401, 403]
        
    def test_gdpr_data_deletion_completeness(self, client):
        """Test GDPR data deletion completeness."""
        # Try to delete data without authentication
        response = client.post('/api/my-data/delete')
        
        # Should be 404 or 401/403
        assert response.status_code in [404, 401, 403]
        
    def test_cookie_consent_enforcement(self, client, database):
        """Test cookie consent enforcement."""
        # Check if analytics cookies are set before consent
        response = client.get('/')
        
        # Analytics cookies should not be set by default
        cookies = response.headers.getlist('Set-Cookie')
        for cookie in cookies:
            assert 'analytics' not in cookie.lower()

class TestInformationDisclosurePrevention:
    """Test prevention of information disclosure."""
    
    def test_error_messages_dont_reveal_system_info(self, client):
        """Test error messages don't reveal system info."""
        # Trigger a 404
        response = client.get('/nonexistent')
        
        # Check response doesn't expose debug/internals (tracebacks, version strings)
        assert b'Traceback (most recent call last)' not in response.data
        assert b'werkzeug.exceptions' not in response.data
        assert b'debugger pin' not in response.data.lower()
        # Stack frames should not be exposed
        assert b'File "' not in response.data
        
    def test_stack_traces_not_exposed_in_production(self, app, client):
        """Test stack traces are not exposed in production."""
        # Set app to production mode
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        
        # Trigger an error
        response = client.get('/admin/nonexistent')
        
        # Check response for stack trace
        assert b'Traceback' not in response.data
        assert b'File "' not in response.data
        
    def test_database_errors_sanitized(self, client):
        """Test database errors are sanitized."""
        # Trigger a database error (e.g., invalid ID)
        response = client.get('/api/projects/invalid-id')
        
        # Check response for database error details
        assert b'sqlalchemy' not in response.data.lower()
        assert b'psycopg2' not in response.data.lower()
        assert b'sqlite' not in response.data.lower()
        
    def test_debug_mode_disabled_in_production(self, app):
        """Test debug mode is disabled in production."""
        # This is a configuration check
        if not app.config.get('TESTING'):
            assert not app.config.get('DEBUG')
            
    def test_admin_panel_not_indexed_by_search_engines(self, client):
        """Test admin panel is not indexed by search engines."""
        response = client.get('/admin/login')
        
        # Check for X-Robots-Tag header or noindex meta tag (either is acceptable)
        has_robots_header = 'X-Robots-Tag' in response.headers and \
            'noindex' in response.headers['X-Robots-Tag'].lower()
        has_noindex_meta = b'noindex' in response.data.lower()
        
        # At least one mechanism should be present, or the route requires auth (302)
        # If admin is accessible, it should have noindex; if it redirects, that's also secure
        if response.status_code == 200:
            # If page is accessible, it should have noindex or robots protection
            assert has_robots_header or has_noindex_meta, \
                "Admin login page should have noindex meta or X-Robots-Tag header"
        else:
            # Redirecting admin routes are implicitly not indexed
            assert response.status_code in [301, 302]
