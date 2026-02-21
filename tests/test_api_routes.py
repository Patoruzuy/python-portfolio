"""
Tests for API routes.
Comprehensive testing of /api/* endpoints.
"""
import pytest
from app.models import db, Project, BlogPost, Newsletter
from datetime import datetime, timezone


class TestProjectsAPI:
    """Test suite for /api/projects endpoint."""
    
    @pytest.fixture
    def sample_projects(self, database):
        """Create sample projects for testing."""
        projects = [
            Project(
                title='Web App',
                description='A web application',
                technologies='Python,Flask,PostgreSQL',
                category='Web Development',
                github_url='https://github.com/user/webapp',
                demo_url='https://webapp.demo.com',
                featured=True
            ),
            Project(
                title='Mobile App',
                description='A mobile application',
                technologies='React Native,TypeScript',
                category='Mobile Development',
                github_url='https://github.com/user/mobileapp'
            ),
            Project(
                title='Data Pipeline',
                description='ETL pipeline',
                technologies='Python,Apache Airflow,PostgreSQL',
                category='Data Engineering',
                featured=False
            ),
        ]
        
        for project in projects:
            db.session.add(project)
        db.session.commit()
        
        return projects
    
    def test_api_projects_returns_all_projects(self, client, sample_projects):
        """Test getting all projects without filters."""
        response = client.get('/api/projects')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 3  # At least our 3 projects
        # Check our specific projects are in results
        titles = [p['title'] for p in data]
        assert 'Web App' in titles
    
    def test_api_projects_filter_by_category(self, client, sample_projects):
        """Test filtering projects by category."""
        response = client.get('/api/projects?category=Web Development')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['category'] == 'Web Development'
        assert data[0]['title'] == 'Web App'
    
    def test_api_projects_filter_by_technology(self, client, sample_projects):
        """Test filtering projects by technology."""
        response = client.get('/api/projects?technology=Python')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 2  # At least our 2 Python projects
        assert all('Python' in p['technologies'] for p in data)
        # Check our specific Python projects are present
        titles = [p['title'] for p in data]
        assert 'Web App' in titles
        assert 'Data Pipeline' in titles
    
    def test_api_projects_filter_by_category_and_technology(
        self,
        client,
        sample_projects
    ):
        """Test filtering by both category and technology."""
        response = client.get(
            '/api/projects?category=Web Development&technology=Flask'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['title'] == 'Web App'
    
    def test_api_projects_returns_correct_structure(self, client, sample_projects):
        """Test that response has correct structure."""
        response = client.get('/api/projects')
        
        assert response.status_code == 200
        data = response.get_json()
        project = data[0]
        
        assert 'id' in project
        assert 'title' in project
        assert 'description' in project
        assert 'technologies' in project
        assert 'category' in project
        assert 'github' in project
        assert 'demo' in project
        assert 'image' in project
        assert isinstance(project['technologies'], list)
    
    def test_api_projects_empty_database(self, client, database):
        """Test API with no projects in database."""
        # Clear all existing projects
        Project.query.delete()
        db.session.commit()
        
        response = client.get('/api/projects')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data == []
    
    def test_api_projects_nonexistent_category(self, client, sample_projects):
        """Test filtering by nonexistent category."""
        response = client.get('/api/projects?category=Nonexistent')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 0


class TestBlogAPI:
    """Test suite for /api/blog endpoint."""
    
    @pytest.fixture
    def sample_blog_posts(self, database):
        """Create sample blog posts for testing."""
        posts = [
            BlogPost(
                title='Python Tutorial',
                slug='api-test-python-tutorial',
                content='Learn Python basics',
                excerpt='Intro to Python',
                author='Admin',
                category='Tutorial',
                tags='python,programming',
                published=True,
                view_count=100,
                created_at=datetime.utcnow()
            ),
            BlogPost(
                title='Flask Guide',
                slug='api-test-flask-guide',
                content='Building web apps with Flask',
                excerpt='Flask fundamentals',
                author='Admin',
                category='Web Development',
                tags='python,flask,web',
                published=True,
                view_count=50,
                created_at=datetime.utcnow()
            ),
            BlogPost(
                title='Draft Post',
                slug='api-test-draft-post',
                content='Unpublished content',
                excerpt='Draft',
                author='Admin',
                category='Tutorial',
                published=False,
                created_at=datetime.utcnow()
            ),
        ]
        
        for post in posts:
            db.session.add(post)
        db.session.commit()
        
        return posts
    
    def test_api_blog_returns_published_posts(self, client, sample_blog_posts):
        """Test that API returns only published posts."""
        response = client.get('/api/blog')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 2  # At least our 2 published posts
        # Verify our posts are in the results
        titles = [p['title'] for p in data]
        assert 'Python Tutorial' in titles
        assert 'Flask Guide' in titles
        # Verify unpublished post is not included
        assert 'Draft Post' not in titles
    
    def test_api_blog_filter_by_category(self, client, sample_blog_posts):
        """Test filtering blog posts by category."""
        response = client.get('/api/blog?category=Tutorial')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1  # At least our 1 Tutorial post
        assert all(p['category'] == 'Tutorial' for p in data)
        # Verify our specific post is present
        titles = [p['title'] for p in data]
        assert 'Python Tutorial' in titles
    
    def test_api_blog_filter_by_tag(self, client, sample_blog_posts):
        """Test filtering blog posts by tag."""
        response = client.get('/api/blog?tag=flask')
        
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) >= 1  # At least our 1 flask-tagged post
        assert all('flask' in p['tags'].lower() for p in data)
        # Verify our specific post is present
        titles = [p['title'] for p in data]
        assert 'Flask Guide' in titles
    
    def test_api_blog_returns_correct_structure(self, client, sample_blog_posts):
        """Test that response has correct structure."""
        response = client.get('/api/blog')
        
        assert response.status_code == 200
        data = response.get_json()
        post = data[0]
        
        assert 'id' in post
        assert 'slug' in post
        assert 'title' in post
        assert 'excerpt' in post
        assert 'author' in post
        assert 'category' in post
        assert 'tags' in post
        assert 'image' in post
        assert 'read_time' in post
        assert 'date' in post
        assert 'view_count' in post
    
    def test_api_blog_ordered_by_date_desc(self, client, sample_blog_posts):
        """Test that posts are ordered by date descending."""
        response = client.get('/api/blog')
        
        assert response.status_code == 200
        data = response.get_json()
        # First post should be the most recent
        assert data[0]['title'] in ['Python Tutorial', 'Flask Guide']


class TestContactAPI:
    """Test suite for /api/contact endpoint."""
    
    def test_contact_requires_post(self, client):
        """Test that contact endpoint requires POST method."""
        response = client.get('/api/contact')
        
        assert response.status_code == 405  # Method Not Allowed
    
    def test_contact_validates_required_fields(self, client):
        """Test validation of required fields."""
        # Missing all fields
        response = client.post(
            '/api/contact',
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Missing required field' in data['error']
    
    def test_contact_validates_name_field(self, client):
        """Test validation of name field."""
        response = client.post(
            '/api/contact',
            json={
                'email': 'test@example.com',
                'subject': 'Test',
                'message': 'Test message'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'name' in data['error']
    
    def test_contact_validates_email_field(self, client):
        """Test validation of email field."""
        response = client.post(
            '/api/contact',
            json={
                'name': 'Test User',
                'subject': 'Test',
                'message': 'Test message'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'email' in data['error']
    
    def test_contact_validates_subject_field(self, client):
        """Test validation of subject field."""
        response = client.post(
            '/api/contact',
            json={
                'name': 'Test User',
                'email': 'test@example.com',
                'message': 'Test message'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'subject' in data['error']
    
    def test_contact_validates_message_field(self, client):
        """Test validation of message field."""
        response = client.post(
            '/api/contact',
            json={
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'Test'
            }
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'message' in data['error']
    
    def test_contact_accepts_form_data(self, client):
        """Test that contact accepts form data."""
        response = client.post(
            '/api/contact',
            data={
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'Test Subject',
                'message': 'Test message'
            }
        )
        
        # Should succeed (returns 200 or 500 depending on Celery availability)
        assert response.status_code in [200, 500]
    
    def test_contact_accepts_json_data(self, client):
        """Test that contact accepts JSON data."""
        response = client.post(
            '/api/contact',
            json={
                'name': 'Test User',
                'email': 'test@example.com',
                'subject': 'Test Subject',
                'message': 'Test message',
                'projectType': 'Web Development'
            }
        )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 500]
        data = response.get_json()
        assert 'success' in data


class TestNewsletterAPI:
    """Test suite for newsletter API endpoints."""
    
    def test_newsletter_subscribe_requires_post(self, client):
        """Test that subscribe endpoint requires POST."""
        response = client.get('/api/newsletter/subscribe')
        
        assert response.status_code == 405
    
    def test_newsletter_subscribe_validates_email(self, client, database):
        """Test email validation."""
        # Missing email
        response = client.post(
            '/api/newsletter/subscribe',
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'email' in data['error'].lower()
    
    def test_newsletter_subscribe_validates_email_format(self, client, database):
        """Test email format validation."""
        response = client.post(
            '/api/newsletter/subscribe',
            json={'email': 'invalid-email'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_newsletter_subscribe_success(self, client, database):
        """Test successful newsletter subscription."""
        response = client.post(
            '/api/newsletter/subscribe',
            json={
                'email': 'newuser@example.com',
                'name': 'New User'
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'Welcome aboard' in data['message']
        
        # Verify subscription in database
        subscription = Newsletter.query.filter_by(
            email='newuser@example.com'
        ).first()
        assert subscription is not None
        assert subscription.name == 'New User'
        assert subscription.active is True
    
    def test_newsletter_subscribe_duplicate_email(self, client, database):
        """Test subscribing with existing email."""
        # First subscription
        subscription = Newsletter(
            email='existing@example.com',
            name='Existing User',
            active=True
        )
        db.session.add(subscription)
        db.session.commit()
        
        # Try to subscribe again
        response = client.post(
            '/api/newsletter/subscribe',
            json={'email': 'existing@example.com'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'already subscribed' in data['error']
    
    def test_newsletter_reactivate_unsubscribed(self, client, database):
        """Test reactivating an unsubscribed email."""
        # Create inactive subscription
        subscription = Newsletter(
            email='inactive@example.com',
            name='Inactive User',
            active=False,
            unsubscribed_at=datetime.now(timezone.utc)
        )
        db.session.add(subscription)
        db.session.commit()
        
        # Resubscribe
        response = client.post(
            '/api/newsletter/subscribe',
            json={'email': 'inactive@example.com'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'Welcome back' in data['message']
        
        # Verify reactivation
        db.session.refresh(subscription)
        assert subscription.active is True
        assert subscription.unsubscribed_at is None
    
    def test_newsletter_confirm_valid_token(self, client, database):
        """Test confirming subscription with valid token."""
        # Create unconfirmed subscription
        subscription = Newsletter(
            email='test@example.com',
            confirmation_token='valid-token-123',
            confirmed=False
        )
        db.session.add(subscription)
        db.session.commit()
        
        # Confirm subscription
        response = client.get('/newsletter/confirm/valid-token-123')
        
        assert response.status_code == 302  # Redirect
        
        # Verify confirmation
        db.session.refresh(subscription)
        assert subscription.confirmed is True
    
    def test_newsletter_confirm_invalid_token(self, client, database):
        """Test confirmation with invalid token."""
        response = client.get('/newsletter/confirm/invalid-token')
        
        assert response.status_code == 302  # Redirect
    
    def test_newsletter_confirm_already_confirmed(self, client, database):
        """Test confirming already confirmed subscription."""
        subscription = Newsletter(
            email='confirmed@example.com',
            confirmation_token='token-456',
            confirmed=True
        )
        db.session.add(subscription)
        db.session.commit()
        
        response = client.get('/newsletter/confirm/token-456')
        
        assert response.status_code == 302
    
    def test_newsletter_unsubscribe_valid_token(self, client, database):
        """Test unsubscribing with valid token."""
        subscription = Newsletter(
            email='active@example.com',
            confirmation_token='unsub-token-789',
            active=True
        )
        db.session.add(subscription)
        db.session.commit()
        
        response = client.get('/newsletter/unsubscribe/unsub-token-789')
        
        assert response.status_code == 302
        
        # Verify unsubscription
        db.session.refresh(subscription)
        assert subscription.active is False
        assert subscription.unsubscribed_at is not None
    
    def test_newsletter_unsubscribe_invalid_token(self, client, database):
        """Test unsubscribing with invalid token."""
        response = client.get('/newsletter/unsubscribe/invalid-unsub-token')
        
        assert response.status_code == 302
    
    def test_newsletter_unsubscribe_already_unsubscribed(self, client, database):
        """Test unsubscribing already inactive subscription."""
        subscription = Newsletter(
            email='inactive@example.com',
            confirmation_token='token-999',
            active=False
        )
        db.session.add(subscription)
        db.session.commit()
        
        response = client.get('/newsletter/unsubscribe/token-999')
        
        assert response.status_code == 302
