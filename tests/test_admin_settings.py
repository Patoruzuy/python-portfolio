"""
Tests for admin settings and configuration routes.
"""
from app.models import OwnerProfile, SiteConfig


class TestOwnerProfile:
    """Test owner profile management."""
    
    def test_owner_profile_requires_auth(self, client, database):
        """Owner profile should require authentication."""
        response = client.get('/admin/owner-profile')
        assert response.status_code in [302, 401, 403]
    
    def test_owner_profile_get_loads_form(self, auth_client, database):
        """Owner profile GET should load form with existing data."""
        response = auth_client.get('/admin/owner-profile')
        assert response.status_code == 200
    
    def test_owner_profile_post_updates_basic_fields(self, auth_client, database):
        """Should update basic owner profile fields."""
        data = {
            'name': 'John Doe',
            'title': 'Senior Developer',
            'bio': 'A passionate developer',
            'email': 'john@example.com',
            'years_experience': '5',
            'projects_completed': '20',
            'contributions': '100',
            'clients_served': '10',
            'certifications': '3'
        }
        
        response = auth_client.post('/admin/owner-profile', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify updates
        owner = OwnerProfile.query.first()
        assert owner.name == 'John Doe'
        assert owner.title == 'Senior Developer'


class TestSiteConfig:
    """Test site configuration management."""
    
    def test_site_config_requires_auth(self, client, database):
        """Site config should require authentication."""
        response = client.get('/admin/site-config')
        assert response.status_code in [302, 401, 403]
    
    def test_site_config_get_loads_form(self, auth_client, database):
        """Site config GET should load form."""
        response = auth_client.get('/admin/site-config')
        assert response.status_code == 200
    
    def test_site_config_post_updates_basic_settings(self, auth_client, database):
        """Should update basic site settings."""
        data = {
            'site_name': 'My Awesome Portfolio',
            'tagline': 'Building amazing things',
            'mail_port': '587'
        }
        
        response = auth_client.post('/admin/site-config', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        config = SiteConfig.query.first()
        assert config.site_name == 'My Awesome Portfolio'


class TestExportConfig:
    """Test configuration export."""
    
    def test_export_config_requires_auth(self, client, database):
        """Export config should require authentication."""
        response = client.get('/admin/export-config')
        assert response.status_code in [302, 401, 403]
    
    def test_export_config_returns_json(self, auth_client, database):
        """Should return JSON with owner and site config."""
        response = auth_client.get('/admin/export-config')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.json
        assert 'exported_at' in data
        assert 'owner_profile' in data
        assert 'site_config' in data
