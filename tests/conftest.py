"""
pytest configuration and fixtures for portfolio application tests.
Provides test client, database setup, and authentication helpers.
"""
import pytest
import os
import tempfile
from app import app as flask_app, db
from models import OwnerProfile, SiteConfig, Product, RaspberryPiProject, BlogPost, PageView
from werkzeug.security import generate_password_hash


@pytest.fixture(scope='session')
def app():
    """Create Flask app configured for testing"""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'cache+memory://',
        'MAIL_SUPPRESS_SEND': True,  # Don't send real emails during tests
        'CACHE_TYPE': 'simple',
    })
    
    return flask_app


@pytest.fixture(scope='function')
def client(app):
    """Create test client for making requests"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create CLI runner for testing CLI commands"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def database(app):
    """Create fresh database for each test"""
    with app.app_context():
        db.create_all()
        
        # Create test data
        _create_test_owner()
        _create_test_site_config()
        _create_test_products()
        _create_test_rpi_projects()
        _create_test_blog_posts()
        
        db.session.commit()
        
        yield db
        
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def auth_client(client, app):
    """Create authenticated test client for admin routes"""
    with app.app_context():
        # Set admin session
        with client.session_transaction() as session:
            session['admin_logged_in'] = True
    
    return client


def _create_test_owner():
    """Create test owner profile"""
    owner = OwnerProfile(
        name='Test Developer',
        title='Senior Python Developer',
        bio='Test bio for portfolio',
        email='test@example.com',
        location='Test City, TC',
        profile_image='/static/images/profile.jpg',
        github='https://github.com/testuser',
        linkedin='https://linkedin.com/in/testuser',
        twitter='https://twitter.com/testuser',
        years_experience=5,
        projects_completed=50,
        contributions=1000,
        clients_served=20,
        certifications=3,
        skills_json='["Python", "Flask", "SQLAlchemy", "JavaScript"]',
        experience_json='[{"title": "Senior Developer", "company": "Test Corp", "years": "2020-Present"}]',
        expertise_json='[{"title": "Backend Development", "description": "Python/Flask expertise"}]'
    )
    db.session.add(owner)


def _create_test_site_config():
    """Create test site configuration"""
    config = SiteConfig(
        site_name='Test Portfolio',
        tagline='Python Developer Portfolio',
        mail_server='smtp.test.com',
        mail_port=587,
        mail_use_tls=True,
        mail_username='test@test.com',
        mail_default_sender='test@test.com',
        mail_recipient='test@test.com',
        blog_enabled=True,
        products_enabled=True,
        analytics_enabled=False
    )
    db.session.add(config)


def _create_test_products():
    """Create test products"""
    products = [
        Product(
            name='Test Product 1',
            description='A test product for unit testing',
            price=29.99,
            type='digital',
            category='software',
            image_url='/static/images/product1.jpg',
            purchase_link='https://test.com/product1'
        ),
        Product(
            name='Test Product 2',
            description='Another test product',
            price=49.99,
            type='service',
            category='service',
            image_url='/static/images/product2.jpg',
            purchase_link='https://test.com/product2'
        )
    ]
    db.session.add_all(products)


def _create_test_rpi_projects():
    """Create test Raspberry Pi projects"""
    projects = [
        RaspberryPiProject(
            title='Test RPi Project 1',
            description='A test Raspberry Pi project',
            image_url='/static/images/rpi1.jpg',
            github_url='https://github.com/test/rpi1',
            technologies='Python,GPIO,Sensors',
            hardware_json='["Raspberry Pi 4", "Temperature Sensor"]',
            features_json='["Real-time monitoring", "GPIO control"]'
        ),
        RaspberryPiProject(
            title='Test RPi Project 2',
            description='Another test project',
            image_url='/static/images/rpi2.jpg',
            github_url='https://github.com/test/rpi2',
            technologies='Python,Camera',
            hardware_json='["Raspberry Pi Zero", "Camera Module"]',
            features_json='["Photo capture", "Video streaming"]'
        )
    ]
    db.session.add_all(projects)


def _create_test_blog_posts():
    """Create test blog posts"""
    posts = [
        BlogPost(
            title='Test Blog Post 1',
            slug='test-blog-post-1',
            content='# Test Post\n\nThis is test content for blog post 1.',
            excerpt='This is a test excerpt',
            author='Test Developer',
            category='Python',
            tags='python,testing,flask',
            image_url='/static/images/blog1.jpg',
            published=True
        ),
        BlogPost(
            title='Test Blog Post 2',
            slug='test-blog-post-2',
            content='# Another Test\n\nThis is test content for blog post 2.',
            excerpt='Another test excerpt',
            author='Test Developer',
            category='Tutorial',
            tags='tutorial,python',
            image_url='/static/images/blog2.jpg',
            published=True
        ),
        BlogPost(
            title='Draft Post',
            slug='draft-post',
            content='# Draft\n\nThis is unpublished.',
            excerpt='Draft excerpt',
            author='Test Developer',
            category='Draft',
            tags='draft',
            image_url='/static/images/draft.jpg',
            published=False
        )
    ]
    db.session.add_all(posts)


@pytest.fixture
def sample_owner_data():
    """Sample data for owner profile creation/update"""
    return {
        'name': 'John Doe',
        'title': 'Full Stack Developer',
        'bio': 'Experienced developer with 10 years',
        'email': 'john@example.com',
        'location': 'San Francisco, CA',
        'github': 'https://github.com/johndoe',
        'linkedin': 'https://linkedin.com/in/johndoe',
        'years_experience': 10,
        'projects_completed': 100,
        'contributions': 5000,
        'clients_served': 50,
        'certifications': 5
    }


@pytest.fixture
def sample_product_data():
    """Sample data for product creation"""
    return {
        'name': 'New Product',
        'description': 'A brand new product',
        'price': 99.99,
        'category': 'software',
        'image_url': '/static/images/new.jpg',
        'purchase_link': 'https://example.com/buy'
    }


@pytest.fixture
def sample_blog_data():
    """Sample data for blog post creation"""
    return {
        'title': 'New Blog Post',
        'content': '# New Post\n\nThis is new content.',
        'excerpt': 'New post excerpt',
        'author': 'Test Author',
        'category': 'Technology',
        'tags': 'tech,new',
        'featured_image': '/static/images/new-blog.jpg',
        'published': True
    }


@pytest.fixture
def mock_celery_task(monkeypatch):
    """Mock Celery task.delay() for testing async calls"""
    class MockTask:
        def __init__(self, task_id='test-task-123'):
            self.id = task_id
            self.state = 'PENDING'
        
        def __call__(self, *args, **kwargs):
            return {'success': True, 'task_id': self.id}
    
    mock_task = MockTask()
    
    def mock_delay(*args, **kwargs):
        return mock_task
    
    # Patch the send_contact_email.delay method
    from tasks import email_tasks
    monkeypatch.setattr(email_tasks.send_contact_email, 'delay', mock_delay)
    
    return mock_task
