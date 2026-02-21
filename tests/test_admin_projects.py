"""
Tests for admin projects and Raspberry Pi management routes.
"""
import json
from unittest.mock import patch
from app.models import db, Project, RaspberryPiProject


class TestProjectsList:
    """Test projects listing page."""
    
    def test_projects_list_requires_auth(self, client, database):
        """Projects list should require authentication."""
        response = client.get('/admin/projects')
        assert response.status_code in [302, 401, 403]
    
    def test_projects_list_loads(self, auth_client, database):
        """Projects list should load with authentication."""
        response = auth_client.get('/admin/projects')
        assert response.status_code == 200


class TestAddProject:
    """Test project creation."""
    
    def test_add_project_get_requires_auth(self, client, database):
        """Add project GET should require authentication."""
        response = client.get('/admin/projects/add')
        assert response.status_code in [302, 401, 403]
    
    def test_add_project_get_loads_form(self, auth_client, database):
        """Add project GET should load form."""
        response = auth_client.get('/admin/projects/add')
        assert response.status_code == 200
    
    def test_add_project_post_creates_project(self, auth_client, database):
        """Should create a new project successfully."""
        data = {
            'title': 'New Project',
            'description': 'A test project',
            'technologies': 'Python, Flask',
            'category': 'Web Application',
            'featured': 'on'
        }
        
        response = auth_client.post('/admin/projects/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify project was created
        project = Project.query.filter_by(title='New Project').first()
        assert project is not None
        assert project.technologies == 'Python, Flask'


class TestEditProject:
    """Test project editing."""
    
    def test_edit_project_get_loads_form(self, auth_client, database):
        """Edit project GET should load form."""
        project = Project.query.first()
        assert project is not None
        
        response = auth_client.get(f'/admin/projects/edit/{project.id}')
        assert response.status_code == 200


class TestDeleteProject:
    """Test project deletion."""
    
    def test_delete_project_success(self, auth_client, database):
        """Should delete project successfully."""
        project = Project(
            title="Project to Delete",
            description="Description",
            technologies="Tech",
            category="Cat"
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id
        
        response = auth_client.post(f'/admin/projects/delete/{project_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify deletion
        deleted = Project.query.get(project_id)
        assert deleted is None


class TestRaspberryPiList:
    """Test Raspberry Pi projects listing."""
    
    def test_raspberry_pi_list_requires_auth(self, client, database):
        """Raspberry Pi list should require authentication."""
        response = client.get('/admin/raspberry-pi')
        assert response.status_code in [302, 401, 403]
    
    def test_raspberry_pi_list_loads(self, auth_client, database):
        """Raspberry Pi list should load."""
        response = auth_client.get('/admin/raspberry-pi')
        assert response.status_code == 200


class TestAddRaspberryPiProject:
    """Test Raspberry Pi project creation."""
    
    def test_add_rpi_get_requires_auth(self, client, database):
        """Add RPi project GET should require authentication."""
        response = client.get('/admin/raspberry-pi/add')
        assert response.status_code in [302, 401, 403]
    
    def test_add_rpi_get_loads_form(self, auth_client, database):
        """Add RPi project GET should load form."""
        response = auth_client.get('/admin/raspberry-pi/add')
        assert response.status_code == 200
    
    @patch('app.routes.admin.projects.validate_video_url')
    def test_add_rpi_project_post_creates_project(self, mock_validate, auth_client, database):
        """Should create Raspberry Pi project successfully."""
        mock_validate.return_value = (True, 'https://youtube.com/embed/abc', 'youtube', None)
        
        data = {
            'title': 'New RPi Project',
            'description': 'A Raspberry Pi project',
            'hardware': 'Raspberry Pi 4',
            'technologies': 'Python',
            'features': 'Motion detection'
        }
        
        response = auth_client.post('/admin/raspberry-pi/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify project was created
        project = RaspberryPiProject.query.filter_by(title='New RPi Project').first()
        assert project is not None


class TestDeleteRaspberryPiProject:
    """Test Raspberry Pi project deletion."""
    
    def test_delete_rpi_success(self, auth_client, database):
        """Should delete RPi project successfully."""
        project = RaspberryPiProject(
            title="RPi to Delete",
            description="Description",
            hardware_json=json.dumps(["RPi 4"]),
            technologies="Python",
            features_json=json.dumps(["Feature"])
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id
        
        response = auth_client.post(f'/admin/raspberry-pi/delete/{project_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify deletion
        deleted = RaspberryPiProject.query.get(project_id)
        assert deleted is None
