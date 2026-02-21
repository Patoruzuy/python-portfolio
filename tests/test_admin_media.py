"""
Tests for admin media upload routes.
"""


class TestImageUpload:
    """Test image upload functionality."""
    
    def test_upload_image_get_requires_auth(self, client, database):
        """Upload image GET should require authentication."""
        response = client.get('/admin/upload-image')
        assert response.status_code in [302, 401, 403]
    
    def test_upload_image_get_loads_form(self, auth_client, database):
        """Upload image GET should load upload form."""
        response = auth_client.get('/admin/upload-image')
        assert response.status_code == 200
