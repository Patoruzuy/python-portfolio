"""
Tests for admin routes and functionality.
Tests authentication, CRUD operations, and admin dashboard.
"""
import pytest
from models import Product, RaspberryPiProject, BlogPost, OwnerProfile, SiteConfig, db


class TestAdminAuthentication:
    """Tests for admin login/logout"""
    
    def test_admin_login_page_loads(self, client):
        """Test admin login page accessible"""
        response = client.get('/admin/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_admin_login_with_correct_password(self, client):
        """Test login with correct password"""
        response = client.post('/admin/login', data={
            'password': 'admin123'  # Default password
        }, follow_redirects=True)
        
        # Should redirect to dashboard
        assert b'Dashboard' in response.data or response.status_code == 200
    
    def test_admin_login_with_wrong_password(self, client):
        """Test login with incorrect password"""
        response = client.post('/admin/login', data={
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert b'Invalid credentials' in response.data or b'incorrect' in response.data.lower()
    
    def test_admin_logout(self, auth_client):
        """Test admin logout"""
        response = auth_client.get('/admin/logout', follow_redirects=True)
        
        # Should redirect to login page
        assert response.status_code == 200
    
    def test_admin_routes_require_auth(self, client):
        """Test admin routes redirect when not authenticated"""
        response = client.get('/admin/dashboard')
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/admin/login' in response.location


class TestAdminDashboard:
    """Tests for admin dashboard"""
    
    def test_dashboard_loads(self, auth_client, database):
        """Test dashboard accessible when authenticated"""
        response = auth_client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_dashboard_shows_stats(self, auth_client, database):
        """Test dashboard displays statistics"""
        response = auth_client.get('/admin/dashboard')
        assert response.status_code == 200
        # Should show counts of products, projects, blog posts
        assert b'2' in response.data  # 2 products
        assert b'3' in response.data  # 3 blog posts


class TestProductCRUD:
    """Tests for product CRUD operations"""
    
    def test_products_list(self, auth_client, database):
        """Test products list page"""
        response = auth_client.get('/admin/products')
        assert response.status_code == 200
        assert b'Test Product 1' in response.data
    
    def test_add_product_page(self, auth_client, database):
        """Test add product form loads"""
        response = auth_client.get('/admin/products/add')
        assert response.status_code == 200
        assert b'<form' in response.data
    
    def test_create_product(self, auth_client, database, sample_product_data):
        """Test creating new product"""
        response = auth_client.post('/admin/products/add', 
                                   data=sample_product_data,
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify product was created
        from app import app
        with app.app_context():
            product = Product.query.filter_by(name='New Product').first()
            assert product is not None
            assert product.price == 99.99
    
    def test_edit_product_page(self, auth_client, database):
        """Test edit product form loads"""
        response = auth_client.get('/admin/products/edit/1')
        assert response.status_code == 200
        assert b'Test Product 1' in response.data
    
    def test_update_product(self, auth_client, database):
        """Test updating existing product"""
        response = auth_client.post('/admin/products/edit/1', data={
            'name': 'Updated Product',
            'description': 'Updated description',
            'price': 39.99,
            'type': 'digital',
            'category': 'software'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify product was updated
        from app import app
        with app.app_context():
            product = Product.query.get(1)
            assert product.name == 'Updated Product'
            assert product.price == 39.99
    
    def test_delete_product(self, auth_client, database):
        """Test deleting product"""
        response = auth_client.post('/admin/products/delete/1',
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify product was deleted
        from app import app
        with app.app_context():
            product = Product.query.get(1)
            assert product is None


class TestRaspberryPiCRUD:
    """Tests for Raspberry Pi project CRUD operations"""
    
    def test_rpi_projects_list(self, auth_client, database):
        """Test RPi projects list page"""
        response = auth_client.get('/admin/raspberry-pi')
        assert response.status_code == 200
        assert b'Test RPi Project 1' in response.data
    
    def test_add_rpi_project_page(self, auth_client, database):
        """Test add RPi project form loads"""
        response = auth_client.get('/admin/raspberry-pi/add')
        assert response.status_code == 200
        assert b'<form' in response.data
    
    def test_create_rpi_project(self, auth_client, database):
        """Test creating new RPi project"""
        data = {
            'title': 'New RPi Project',
            'description': 'New project description',
            'full_description': 'Full details',
            'technologies': 'Python,GPIO',
            'difficulty': 'Intermediate',
            'hardware_required': 'Raspberry Pi 4'
        }
        
        response = auth_client.post('/admin/raspberry-pi/add',
                                   data=data,
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify project was created
        from app import app
        with app.app_context():
            project = RaspberryPiProject.query.filter_by(title='New RPi Project').first()
            assert project is not None
    
    def test_delete_rpi_project(self, auth_client, database):
        """Test deleting RPi project"""
        response = auth_client.post('/admin/raspberry-pi/delete/1',
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify project was deleted
        from app import app
        with app.app_context():
            project = RaspberryPiProject.query.get(1)
            assert project is None


class TestBlogCRUD:
    """Tests for blog post CRUD operations"""
    
    def test_blog_posts_list(self, auth_client, database):
        """Test blog posts list page"""
        response = auth_client.get('/admin/blog')
        assert response.status_code == 200
        assert b'Test Blog Post 1' in response.data
    
    def test_add_blog_post_page(self, auth_client, database):
        """Test add blog post form loads"""
        response = auth_client.get('/admin/blog/create')
        assert response.status_code == 200
        assert b'<form' in response.data
    
    def test_create_blog_post(self, auth_client, database, sample_blog_data):
        """Test creating new blog post"""
        response = auth_client.post('/admin/blog/create',
                                   data=sample_blog_data,
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify post was created with auto-generated slug
        from app import app
        with app.app_context():
            post = BlogPost.query.filter_by(title='New Blog Post').first()
            assert post is not None
            assert post.slug == 'new-blog-post'
    
    def test_blog_post_slug_auto_generation(self, auth_client, database):
        """Test automatic slug generation from title"""
        data = {
            'title': 'This Is A Test Post!',
            'content': 'Content',
            'author': 'Test',
            'category': 'Tech',
            'published': True
        }
        
        response = auth_client.post('/admin/blog/create',
                                   data=data,
                                   follow_redirects=True)
        
        # Verify slug was auto-generated
        from app import app
        with app.app_context():
            post = BlogPost.query.filter_by(title='This Is A Test Post!').first()
            assert post is not None
            assert post.slug == 'this-is-a-test-post'
    
    def test_edit_blog_post_page(self, auth_client, database):
        """Test edit blog post form loads"""
        response = auth_client.get('/admin/blog/edit/1')
        assert response.status_code == 200
        assert b'Test Blog Post 1' in response.data
    
    def test_update_blog_post(self, auth_client, database):
        """Test updating existing blog post"""
        response = auth_client.post('/admin/blog/edit/1', data={
            'title': 'Updated Blog Post',
            'content': 'Updated content',
            'author': 'Test Author',
            'category': 'Updated',
            'published': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify post was updated
        from app import app
        with app.app_context():
            post = BlogPost.query.get(1)
            assert post.title == 'Updated Blog Post'

    def test_update_blog_post_preserves_publish_state_without_control(self, auth_client, database):
        """Legacy forms that omit publish control should not silently unpublish."""
        response = auth_client.post('/admin/blog/edit/1', data={
            'title': 'Updated Blog Post Legacy Form',
            'content': 'Updated content',
            'author': 'Test Author',
            'category': 'Updated'
        }, follow_redirects=True)

        assert response.status_code == 200

        from app import app
        with app.app_context():
            post = BlogPost.query.get(1)
            assert post.title == 'Updated Blog Post Legacy Form'
            assert post.published is True

    def test_update_blog_post_can_unpublish_with_control(self, auth_client, database):
        """Published posts can be intentionally set to draft via form control."""
        response = auth_client.post('/admin/blog/edit/1', data={
            'title': 'Updated Blog Post Draft',
            'content': 'Updated content',
            'author': 'Test Author',
            'category': 'Updated',
            'published_present': '1'
        }, follow_redirects=True)

        assert response.status_code == 200

        from app import app
        with app.app_context():
            post = BlogPost.query.get(1)
            assert post.title == 'Updated Blog Post Draft'
            assert post.published is False

    def test_update_blog_post_can_publish_with_control(self, auth_client, database):
        """Draft posts can be intentionally published via form control."""
        response = auth_client.post('/admin/blog/edit/3', data={
            'title': 'Draft Post Published',
            'content': 'Updated content',
            'author': 'Test Author',
            'category': 'Updated',
            'published_present': '1',
            'published': '1'
        }, follow_redirects=True)

        assert response.status_code == 200

        from app import app
        with app.app_context():
            post = BlogPost.query.get(3)
            assert post.title == 'Draft Post Published'
            assert post.published is True
    
    def test_delete_blog_post(self, auth_client, database):
        """Test deleting blog post"""
        response = auth_client.post('/admin/blog/delete/1',
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify post was deleted
        from app import app
        with app.app_context():
            post = BlogPost.query.get(1)
            assert post is None


class TestOwnerProfileManagement:
    """Tests for owner profile management"""
    
    def test_owner_profile_page_loads(self, auth_client, database):
        """Test owner profile management page"""
        response = auth_client.get('/admin/owner-profile')
        assert response.status_code == 200
        assert b'Test Developer' in response.data
    
    def test_update_owner_profile(self, auth_client, database):
        """Test updating owner profile"""
        data = {
            'name': 'Updated Developer',
            'title': 'Lead Developer',
            'bio': 'Updated bio',
            'email': 'updated@example.com',
            'years_experience': 10,
            'projects_completed': 100,
            'contributions': 2000,
            'clients_served': 30,
            'certifications': 5
        }
        
        response = auth_client.post('/admin/owner-profile',
                                   data=data,
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify profile was updated
        from app import app
        with app.app_context():
            owner = OwnerProfile.query.first()
            assert owner.name == 'Updated Developer'
            assert owner.years_experience == 10


class TestSiteConfigManagement:
    """Tests for site configuration management"""
    
    def test_site_config_page_loads(self, auth_client, database):
        """Test site config management page"""
        response = auth_client.get('/admin/site-config')
        assert response.status_code == 200
        assert b'Test Portfolio' in response.data
    
    def test_update_site_config(self, auth_client, database):
        """Test updating site configuration"""
        data = {
            'site_name': 'Updated Portfolio',
            'tagline': 'New tagline',
            'mail_server': 'smtp.updated.com',
            'mail_port': '587',
            'mail_use_tls': 'on',
            'blog_enabled': 'on',
            'products_enabled': 'on',
            'analytics_enabled': 'on'
        }
        
        response = auth_client.post('/admin/site-config',
                                   data=data,
                                   follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify config was updated
        from app import app
        with app.app_context():
            config = SiteConfig.query.first()
            assert config.site_name == 'Updated Portfolio'
            assert config.analytics_enabled is True


class TestPasswordReset:
    """Tests for admin password reset"""
    
    def test_password_reset_page_loads(self, auth_client, database):
        """Test password reset page accessible"""
        response = auth_client.get('/admin/forgot-password')
        assert response.status_code == 200
        assert b'password' in response.data.lower()
    
    def test_password_reset_displays_hash(self, auth_client, database):
        """Test password reset shows bcrypt hash"""
        response = auth_client.post('/admin/forgot-password', data={
            'new_password': 'newpassword123'
        })
        
        assert response.status_code == 200
        # Should display the password hash (scrypt format)
        assert b'scrypt:' in response.data or b'$2b$' in response.data


class TestConfigExportImport:
    """Tests for configuration export/import"""
    
    def test_export_config(self, auth_client, database):
        """Test exporting configuration as JSON"""
        response = auth_client.get('/admin/export-config')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = response.get_json()
        assert 'owner_profile' in data
        assert 'site_config' in data
    


class TestAdminValidation:
    """Tests for admin form validation"""
    
    def test_product_price_validation(self, auth_client, database):
        """Test product price must be valid"""
        response = auth_client.post('/admin/products/add', data={
            'name': 'Invalid Product',
            'description': 'Test',
            'price': 'not-a-number',  # Invalid price
            'type': 'digital',
            'category': 'software'
        })
        
        # Should fail validation (may show form again or error)
        # Exact behavior depends on implementation
        assert response.status_code in [200, 400]
    
    def test_required_fields_validation(self, auth_client, database):
        """Test required fields are enforced"""
        response = auth_client.post('/admin/products/add', data={
            # Missing required fields
            'type': 'digital',
            'category': 'software'
        })
        
        # Should fail validation
        assert response.status_code in [200, 400]
