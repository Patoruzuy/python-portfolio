"""
Tests for project service layer.
"""
import pytest
from services.project_service import ProjectService, RaspberryPiService, project_service, rpi_service
from models import Project, RaspberryPiProject, db


@pytest.fixture
def proj_service():
    """Get project service instance."""
    return ProjectService()


@pytest.fixture
def rpi_svc():
    """Get Raspberry Pi service instance."""
    return RaspberryPiService()


@pytest.fixture
def sample_project(database):
    """Create sample project for testing."""
    project = Project(
        title='Test Project',
        description='Test description',
        technologies='Python,Flask,PostgreSQL',
        category='Web Development',
        github_url='https://github.com/test/project',
        demo_url='https://demo.test.com',
        featured=True
    )
    db.session.add(project)
    db.session.commit()
    return project


@pytest.fixture
def sample_rpi_project(database):
    """Create sample Raspberry Pi project for testing."""
    project = RaspberryPiProject(
        title='Test RPi Project',
        description='Test RPi description',
        hardware_json='["Raspberry Pi 4", "Camera Module"]',
        technologies='Python,GPIO,OpenCV'
    )
    db.session.add(project)
    db.session.commit()
    return project


class TestGetAllProjects:
    """Test retrieving all projects."""
    
    def test_get_all_projects_returns_list(self, database, proj_service):
        """Should return list of projects."""
        result = proj_service.get_all_projects()
        assert isinstance(result, list)
    
    def test_get_all_projects_returns_all(self, database, proj_service, sample_project):
        """Should return all projects."""
        # Create additional project
        project2 = Project(title='Project 2', description='Desc 2', technologies='JavaScript', category='Mobile')
        db.session.add(project2)
        db.session.commit()
        
        result = proj_service.get_all_projects()
        # Fixture creates 3 projects, sample_project adds 1, we add 1 = 5 total
        assert len(result) == 5
        assert sample_project in result


class TestGetFeaturedProjects:
    """Test retrieving featured projects."""
    
    def test_get_featured_projects_returns_list(self, database, proj_service):
        """Should return list of projects."""
        result = proj_service.get_featured_projects()
        assert isinstance(result, list)
    
    def test_get_featured_projects_filters_featured(self, database, proj_service):
        """Should return only featured projects."""
        featured = Project(title='Featured', description='Desc', technologies='Python', featured=True, category='Web')
        not_featured = Project(title='Not Featured', description='Desc', technologies='Java', featured=False, category='Web')
        db.session.add_all([featured, not_featured])
        db.session.commit()
        
        result = proj_service.get_featured_projects()
        # Fixture creates 2 featured projects + our 1 featured = 3 total
        assert len(result) == 3
        assert any(p.title == 'Featured' for p in result)
    
    def test_get_featured_projects_respects_limit(self, database, proj_service):
        """Should respect limit parameter."""
        for i in range(5):
            project = Project(title=f'Featured {i}', description='Desc', technologies='Python', featured=True, category='Web')
            db.session.add(project)
        db.session.commit()
        
        result = proj_service.get_featured_projects(limit=3)
        assert len(result) == 3


class TestGetByCategory:
    """Test retrieving projects by category."""
    
    def test_get_by_category_filters_correctly(self, database, proj_service):
        """Should return projects matching category."""
        web_project = Project(title='Web App', description='Desc', technologies='Python', category='Web Development')
        mobile_project = Project(title='Mobile App', description='Desc', technologies='Kotlin', category='Mobile')
        db.session.add_all([web_project, mobile_project])
        db.session.commit()
        
        result = proj_service.get_by_category('Web Development')
        assert len(result) == 1
        assert result[0].title == 'Web App'
    
    def test_get_by_category_returns_empty_if_none(self, database, proj_service):
        """Should return empty list if no matches."""
        result = proj_service.get_by_category('Nonexistent Category')
        assert result == []


class TestGetByTechnology:
    """Test retrieving projects by technology."""
    
    def test_get_by_technology_filters_correctly(self, database, proj_service):
        """Should return projects using technology."""
        python_project = Project(title='Python App', description='Desc', technologies='Python,Flask', category='Web')
        java_project = Project(title='Java App', description='Desc', technologies='Java,Spring', category='Web')
        db.session.add_all([python_project, java_project])
        db.session.commit()
        
        result = proj_service.get_by_technology('Flask')
        # Fixture has 1 project with Flask + our new one = 2 total
        assert len(result) == 2
        assert any(p.title == 'Python App' for p in result)
    
    def test_get_by_technology_returns_empty_if_none(self, database, proj_service):
        """Should return empty list if no matches."""
        result = proj_service.get_by_technology('NonexistentTech')
        assert result == []


class TestGetById:
    """Test retrieving project by ID."""
    
    def test_get_by_id_returns_project(self, database, proj_service, sample_project):
        """Should return project by ID."""
        result = proj_service.get_by_id(sample_project.id)
        
        assert result is not None
        assert result.id == sample_project.id
        assert result.title == 'Test Project'
    
    def test_get_by_id_returns_none_not_found(self, database, proj_service):
        """Should return None if project not found."""
        result = proj_service.get_by_id(99999)
        assert result is None


class TestCreateProject:
    """Test project creation."""
    
    def test_create_project_success(self, database, proj_service):
        """Should create new project."""
        data = {
            'title': 'New Project',
            'description': 'New description',
            'technologies': 'React,Node.js',
            'category': 'Web Development',
            'featured': False
        }
        
        project = proj_service.create_project(data)
        
        assert project is not None
        assert project.id is not None
        assert project.title == 'New Project'
        assert project.technologies == 'React,Node.js'
    
    def test_create_project_saves_to_db(self, database, proj_service):
        """Should save project to database."""
        data = {
            'title': 'Saved Project',
            'description': 'Description',
            'technologies': 'Swift',
            'category': 'Mobile'
        }
        
        project = proj_service.create_project(data)
        
        # Verify in database
        saved_project = Project.query.get(project.id)
        assert saved_project is not None
        assert saved_project.title == 'Saved Project'


class TestUpdateProject:
    """Test project updates."""
    
    def test_update_project_success(self, database, proj_service, sample_project):
        """Should update project fields."""
        data = {
            'title': 'Updated Title',
            'description': 'Updated description'
        }
        
        updated = proj_service.update_project(sample_project.id, data)
        
        assert updated is not None
        assert updated.title == 'Updated Title'
        assert updated.description == 'Updated description'
    
    def test_update_project_persists_changes(self, database, proj_service, sample_project):
        """Should persist changes to database."""
        data = {'title': 'Persisted Title'}
        proj_service.update_project(sample_project.id, data)
        
        # Verify in database
        project = Project.query.get(sample_project.id)
        assert project.title == 'Persisted Title'
    
    def test_update_project_returns_none_not_found(self, database, proj_service):
        """Should return None if project not found."""
        result = proj_service.update_project(99999, {'title': 'Test'})
        assert result is None


class TestDeleteProject:
    """Test project deletion."""
    
    def test_delete_project_success(self, database, proj_service, sample_project):
        """Should delete project."""
        project_id = sample_project.id
        result = proj_service.delete_project(project_id)
        
        assert result is True
        assert Project.query.get(project_id) is None
    
    def test_delete_project_not_found(self, database, proj_service):
        """Should return False if project not found."""
        result = proj_service.delete_project(99999)
        assert result is False


class TestToDict:
    """Test project serialization."""
    
    def test_to_dict_returns_dict(self, database, proj_service, sample_project):
        """Should return dictionary."""
        result = proj_service.to_dict(sample_project)
        assert isinstance(result, dict)
    
    def test_to_dict_contains_expected_fields(self, database, proj_service, sample_project):
        """Should contain all expected fields."""
        result = proj_service.to_dict(sample_project)
        
        assert 'id' in result
        assert 'title' in result
        assert 'description' in result
        assert 'technologies' in result
        assert 'category' in result
        assert 'image' in result
        assert 'github' in result
        assert 'demo' in result
        assert 'featured' in result
    
    def test_to_dict_splits_technologies(self, database, proj_service, sample_project):
        """Should split technologies into list."""
        result = proj_service.to_dict(sample_project)
        
        assert isinstance(result['technologies'], list)
        assert 'Python' in result['technologies']
        assert 'Flask' in result['technologies']
    
    def test_to_dict_handles_empty_technologies(self, database, proj_service):
        """Should handle empty technologies string."""
        project = Project(title='No Tech', description='Desc', technologies='', category='Web')
        db.session.add(project)
        db.session.commit()
        
        result = proj_service.to_dict(project)
        assert result['technologies'] == []


class TestRaspberryPiGetAllProjects:
    """Test retrieving all RPi projects."""
    
    def test_get_all_projects_returns_list(self, database, rpi_svc):
        """Should return list of projects."""
        result = rpi_svc.get_all_projects()
        assert isinstance(result, list)
    
    def test_get_all_projects_returns_all(self, database, rpi_svc, sample_rpi_project):
        """Should return all RPi projects."""
        project2 = RaspberryPiProject(title='RPi 2', description='Desc 2', technologies='Python')
        db.session.add(project2)
        db.session.commit()
        
        result = rpi_svc.get_all_projects()
        # Fixture creates 2 RPi projects + sample adds 1 + we add 1 = 4 total
        assert len(result) == 4
        assert any(p.title == 'RPi 2' for p in result)


class TestRaspberryPiGetById:
    """Test retrieving RPi project by ID."""
    
    def test_get_by_id_returns_project(self, database, rpi_svc, sample_rpi_project):
        """Should return RPi project by ID."""
        result = rpi_svc.get_by_id(sample_rpi_project.id)
        
        assert result is not None
        assert result.id == sample_rpi_project.id
        assert result.title == 'Test RPi Project'
    
    def test_get_by_id_returns_none_not_found(self, database, rpi_svc):
        """Should return None if project not found."""
        result = rpi_svc.get_by_id(99999)
        assert result is None


class TestRaspberryPiCreateProject:
    """Test RPi project creation."""
    
    def test_create_project_success(self, database, rpi_svc):
        """Should create new RPi project."""
        data = {
            'title': 'New RPi Project',
            'description': 'New RPi description',
            'hardware_json': '["Pi Zero", "Sensor"]',
            'technologies': 'Python,GPIO'
        }
        
        project = rpi_svc.create_project(data)
        
        assert project is not None
        assert project.id is not None
        assert project.title == 'New RPi Project'
    
    def test_create_project_saves_to_db(self, database, rpi_svc):
        """Should save RPi project to database."""
        data = {
            'title': 'Saved RPi',
            'description': 'Description',
            'technologies': 'Python'
        }
        
        project = rpi_svc.create_project(data)
        
        # Verify in database
        saved = RaspberryPiProject.query.get(project.id)
        assert saved is not None
        assert saved.title == 'Saved RPi'


class TestRaspberryPiUpdateProject:
    """Test RPi project updates."""
    
    def test_update_project_success(self, database, rpi_svc, sample_rpi_project):
        """Should update RPi project fields."""
        data = {
            'title': 'Updated RPi Title',
            'description': 'Updated RPi description'
        }
        
        updated = rpi_svc.update_project(sample_rpi_project.id, data)
        
        assert updated is not None
        assert updated.title == 'Updated RPi Title'
    
    def test_update_project_returns_none_not_found(self, database, rpi_svc):
        """Should return None if project not found."""
        result = rpi_svc.update_project(99999, {'title': 'Test'})
        assert result is None


class TestRaspberryPiDeleteProject:
    """Test RPi project deletion."""
    
    def test_delete_project_success(self, database, rpi_svc, sample_rpi_project):
        """Should delete RPi project."""
        project_id = sample_rpi_project.id
        result = rpi_svc.delete_project(project_id)
        
        assert result is True
        assert RaspberryPiProject.query.get(project_id) is None
    
    def test_delete_project_not_found(self, database, rpi_svc):
        """Should return False if project not found."""
        result = rpi_svc.delete_project(99999)
        assert result is False


class TestGlobalInstances:
    """Test global service instances."""
    
    def test_project_service_instance_exists(self):
        """Should have global project_service instance."""
        assert project_service is not None
        assert isinstance(project_service, ProjectService)
    
    def test_rpi_service_instance_exists(self):
        """Should have global rpi_service instance."""
        assert rpi_service is not None
        assert isinstance(rpi_service, RaspberryPiService)
