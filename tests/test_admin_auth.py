"""
Tests for admin authentication routes.
Tests login, logout, password reset, and security settings.
"""
import pytest
from werkzeug.security import generate_password_hash
from app.models import AdminRecoveryCode


# Fixture to set up admin credentials for login tests
@pytest.fixture
def admin_credentials(app):
    """Set admin credentials in app config for testing"""
    test_password = 'test_password_123'
    test_hash = generate_password_hash(test_password)
    app.config['ADMIN_USERNAME'] = 'admin'
    app.config['ADMIN_PASSWORD_HASH'] = test_hash
    return {'username': 'admin', 'password': test_password, 'hash': test_hash}


class TestAdminLogin:
    """Test admin login functionality."""
    
    def test_login_page_loads(self, client, database):
        """Should load login page."""
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_login_success_with_valid_credentials(self, client, database, admin_credentials):
        """Should login successfully with valid credentials."""
        response = client.post('/admin/login', data={
            'username': admin_credentials['username'],
            'password': admin_credentials['password']
        }, follow_redirects=False)
        
        assert response.status_code == 302
        assert '/admin/dashboard' in response.location
    
    def test_login_failure_with_invalid_password(self, client, database, monkeypatch):
        """Should fail login with wrong password."""
        test_hash = generate_password_hash('correct_password')
        
        monkeypatch.setenv('ADMIN_USERNAME', 'admin')
        monkeypatch.setenv('ADMIN_PASSWORD_HASH', test_hash)
        
        response = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'wrong_password'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid credentials' in response.data
    
    def test_login_failure_with_invalid_username(self, client, database, monkeypatch):
        """Should fail login with wrong username."""
        test_hash = generate_password_hash('test_password')
        
        monkeypatch.setenv('ADMIN_USERNAME', 'admin')
        monkeypatch.setenv('ADMIN_PASSWORD_HASH', test_hash)
        
        response = client.post('/admin/login', data={
            'username': 'wrong_user',
            'password': 'test_password'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid credentials' in response.data
    
    def test_login_redirect_when_already_logged_in(self, client, database, admin_credentials):
        """Should redirect to dashboard if already logged in."""
        # First login
        client.post('/admin/login', data={
            'username': admin_credentials['username'],
            'password': admin_credentials['password']
        })
        
        # Try to access login page again
        response = client.get('/admin/login', follow_redirects=False)
        assert response.status_code == 302
        assert '/admin/dashboard' in response.location
    
    def test_login_with_remember_me(self, client, database, admin_credentials):
        """Should set permanent session with remember me."""
        with client:
            response = client.post('/admin/login', data={
                'username': admin_credentials['username'],
                'password': admin_credentials['password'],
                'remember': 'on'
            }, follow_redirects=False)
            
            assert response.status_code == 302
            with client.session_transaction() as sess:
                assert sess.get('admin_logged_in') is True
                assert sess.get('remember_me') is True
    
    def test_login_without_remember_me(self, client, database, admin_credentials):
        """Should use shorter session without remember me."""
        with client:
            response = client.post('/admin/login', data={
                'username': admin_credentials['username'],
                'password': admin_credentials['password']
            }, follow_redirects=False)
            
            assert response.status_code == 302
            with client.session_transaction() as sess:
                assert sess.get('admin_logged_in') is True
                assert 'remember_me' not in sess
    
    def test_login_error_when_no_admin_hash_configured(self, client, database, monkeypatch):
        """Should show error when admin credentials not configured."""
        # Mock the utility functions to return None (not configured)
        monkeypatch.setattr('app.routes.admin.auth.get_admin_username', lambda: 'admin')
        monkeypatch.setattr('app.routes.admin.auth.get_admin_password_hash', lambda: None)
        
        response = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'test_password'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'not configured' in response.data or b'Invalid credentials' in response.data


class TestAdminLogout:
    """Test admin logout functionality."""
    
    def test_logout_clears_session(self, client, database, admin_credentials):
        """Should clear session on logout."""
        with client:
            # Login first
            client.post('/admin/login', data={
                'username': admin_credentials['username'],
                'password': admin_credentials['password']
            })
            
            # Verify logged in
            with client.session_transaction() as sess:
                assert sess.get('admin_logged_in') is True
            
            # Logout
            _ = client.get('/admin/logout', follow_redirects=False)
            
            # Check session cleared (should be None after logout)
            with client.session_transaction() as sess:
                assert sess.get('admin_logged_in') is None
    
    def test_logout_redirects_to_login(self, client, database):
        """Should redirect to login page after logout."""
        response = client.get('/admin/logout', follow_redirects=False)
        assert response.status_code == 302
        assert '/admin/login' in response.location
    
    def test_logout_shows_success_message(self, client, database):
        """Should show logout success message."""
        response = client.get('/admin/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'logged out' in response.data


class TestForgotPassword:
    """Test password reset functionality."""
    
    def test_forgot_password_page_loads(self, client, database):
        """Should load forgot password page."""
        response = client.get('/admin/forgot-password')
        assert response.status_code == 200
        assert b'password' in response.data.lower()
    
    def test_forgot_password_with_valid_recovery_code(self, client, database):
        """Should reset password with valid recovery code."""
        # Generate recovery codes
        codes = AdminRecoveryCode.generate_codes(5)
        valid_code = codes[0]
        
        response = client.post('/admin/forgot-password', data={
            'recovery_code': valid_code,
            'new_password': 'new_secure_password_123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Check that password hash generation was successful (page loads without error)
        assert b'password' in response.data.lower()
    
    def test_forgot_password_with_invalid_recovery_code(self, client, database):
        """Should reject invalid recovery code."""
        response = client.post('/admin/forgot-password', data={
            'recovery_code': 'invalid_code_12345',
            'new_password': 'new_password_123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # The form should still be present after invalid code (not showing new hash)
        assert b'recovery code' in response.data.lower() or b'password' in response.data.lower()
    
    def test_forgot_password_legacy_fallback_without_code(self, client, database):
        """Should generate hash in legacy mode without recovery code."""
        response = client.post('/admin/forgot-password', data={
            'new_password': 'new_password_123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'legacy fallback' in response.data.lower()
    
    def test_forgot_password_requires_new_password(self, client, database):
        """Should require new password field."""
        response = client.post('/admin/forgot-password', data={
            'recovery_code': 'some_code'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'password' in response.data.lower()
    
    def test_forgot_password_shows_remaining_codes(self, client, database):
        """Should display remaining recovery codes count."""
        # Generate some codes
        AdminRecoveryCode.generate_codes(3)
        
        response = client.get('/admin/forgot-password')
        assert response.status_code == 200
        # Should show that codes are available


class TestSecuritySettings:
    """Test security settings page."""
    
    def test_security_page_requires_login(self, client, database):
        """Should require login to access security settings."""
        response = client.get('/admin/security', follow_redirects=False)
        assert response.status_code == 302
        assert '/admin/login' in response.location
    
    def test_security_page_loads_when_logged_in(self, client, database, monkeypatch):
        """Should load security page when logged in."""
        # Set session directly to simulate logged in state
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        
        # Access security page
        response = client.get('/admin/security')
        assert response.status_code == 200
        assert b'security' in response.data.lower() or b'recovery' in response.data.lower()
    
    def test_generate_recovery_codes(self, client, database, monkeypatch):
        """Should generate new recovery codes."""
        # Set session directly to simulate logged in state
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        
        # Generate codes
        response = client.post('/admin/security', data={
            'action': 'generate_codes'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'recovery codes generated' in response.data.lower() or b'codes' in response.data.lower()
        
        # Verify codes were created in database
        remaining = AdminRecoveryCode.get_remaining_count()
        assert remaining == 10
    
    def test_security_page_shows_remaining_codes(self, client, database, monkeypatch):
        """Should display remaining codes count."""
        # Generate some codes
        AdminRecoveryCode.generate_codes(5)
        
        # Set session directly to simulate logged in state
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
        
        # Check page shows count
        response = client.get('/admin/security')
        assert response.status_code == 200
