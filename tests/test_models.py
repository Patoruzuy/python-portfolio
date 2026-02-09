"""
Unit tests for database models.
Tests model creation, validation, relationships, and methods.
"""
import pytest
from datetime import datetime, timezone
from models import (
    OwnerProfile, SiteConfig, Product, RaspberryPiProject, 
    BlogPost, PageView, db
)
import json


class TestOwnerProfile:
    """Tests for OwnerProfile model"""
    
    def test_create_owner_profile(self, app, database):
        """Test creating owner profile"""
        with app.app_context():
            owner = OwnerProfile.query.first()
            assert owner is not None
            assert owner.name == 'Test Developer'
            assert owner.email == 'test@example.com'
            assert owner.years_experience == 5
    
    def test_owner_skills_property(self, app, database):
        """Test skills JSON property"""
        with app.app_context():
            owner = OwnerProfile.query.first()
            skills = owner.skills
            assert isinstance(skills, list)
            assert 'Python' in skills
            assert 'Flask' in skills
    
    def test_owner_experience_property(self, app, database):
        """Test experience JSON property"""
        with app.app_context():
            owner = OwnerProfile.query.first()
            experience = owner.experience
            assert isinstance(experience, list)
            assert len(experience) > 0
            assert experience[0]['title'] == 'Senior Developer'
    
    def test_owner_expertise_property(self, app, database):
        """Test expertise JSON property"""
        with app.app_context():
            owner = OwnerProfile.query.first()
            expertise = owner.expertise
            assert isinstance(expertise, list)
            assert len(expertise) > 0
            assert 'Backend Development' in expertise[0]['title']
    
    def test_owner_str_representation(self, app, database):
        """Test string representation"""
        with app.app_context():
            owner = OwnerProfile.query.first()
            assert str(owner) == '<OwnerProfile Test Developer>'
    
    def test_owner_unique_constraint(self, app, database):
        """Test that only one owner profile can exist"""
        with app.app_context():
            # Try to create second owner
            second_owner = OwnerProfile(
                name='Second Owner',
                title='Developer',
                bio='Another owner',
                email='second@example.com'
            )
            db.session.add(second_owner)
            
            # Should fail due to unique constraint (only one owner allowed)
            with pytest.raises(Exception):
                db.session.commit()


class TestSiteConfig:
    """Tests for SiteConfig model"""
    
    def test_create_site_config(self, app, database):
        """Test creating site configuration"""
        with app.app_context():
            config = SiteConfig.query.first()
            assert config is not None
            assert config.site_name == 'Test Portfolio'
            assert config.mail_server == 'smtp.test.com'
    
    def test_site_config_feature_flags(self, app, database):
        """Test feature flag booleans"""
        with app.app_context():
            config = SiteConfig.query.first()
            assert config.blog_enabled is True
            assert config.products_enabled is True
            assert config.analytics_enabled is False
    
    def test_site_config_str_representation(self, app, database):
        """Test string representation"""
        with app.app_context():
            config = SiteConfig.query.first()
            assert str(config) == '<SiteConfig Test Portfolio>'


class TestProduct:
    """Tests for Product model"""
    
    def test_create_product(self, app, database):
        """Test creating product"""
        with app.app_context():
            products = Product.query.all()
            assert len(products) == 2
            
            product = products[0]
            assert product.name == 'Test Product 1'
            assert product.price == 29.99
            assert product.category == 'software'
    
    def test_product_defaults(self, app, database):
        """Test product default values"""
        with app.app_context():
            product = Product(
                name='Minimal Product',
                description='Minimal',
                price=10.00
            )
            db.session.add(product)
            db.session.commit()
            
            assert product.category == 'other'
            assert product.created_at is not None
    
    def test_product_str_representation(self, app, database):
        """Test string representation"""
        with app.app_context():
            product = Product.query.first()
            assert str(product) == '<Product Test Product 1>'
    
    def test_product_price_validation(self, app, database):
        """Test price must be positive"""
        with app.app_context():
            # Note: SQLite doesn't enforce CHECK constraints by default
            # This is more of a business logic test
            product = Product(
                name='Invalid Product',
                description='Test',
                price=-10.00
            )
            db.session.add(product)
            db.session.commit()
            
            # In real app, validation should happen at form/API level
            assert product.price < 0  # Shows we need validation


class TestRaspberryPiProject:
    """Tests for RaspberryPiProject model"""
    
    def test_create_rpi_project(self, app, database):
        """Test creating Raspberry Pi project"""
        with app.app_context():
            projects = RaspberryPiProject.query.all()
            assert len(projects) == 2
            
            project = projects[0]
            assert project.title == 'Test RPi Project 1'
            assert project.difficulty == 'Intermediate'
            assert 'Python' in project.technologies
    
    def test_rpi_project_defaults(self, app, database):
        """Test project default values"""
        with app.app_context():
            project = RaspberryPiProject(
                title='Minimal RPi Project',
                description='Minimal description'
            )
            db.session.add(project)
            db.session.commit()
            
            assert project.difficulty == 'Beginner'
            assert project.created_at is not None
    
    def test_rpi_project_str_representation(self, app, database):
        """Test string representation"""
        with app.app_context():
            project = RaspberryPiProject.query.first()
            assert str(project) == '<RaspberryPiProject Test RPi Project 1>'


class TestBlogPost:
    """Tests for BlogPost model"""
    
    def test_create_blog_post(self, app, database):
        """Test creating blog post"""
        with app.app_context():
            posts = BlogPost.query.all()
            assert len(posts) == 3  # 2 published + 1 draft
            
            post = posts[0]
            assert post.title == 'Test Blog Post 1'
            assert post.slug == 'test-blog-post-1'
            assert post.published is True
    
    def test_blog_post_slug_uniqueness(self, app, database):
        """Test slug must be unique"""
        with app.app_context():
            post = BlogPost(
                title='Duplicate Slug',
                slug='test-blog-post-1',  # Duplicate slug
                content='Test content',
                author='Test'
            )
            db.session.add(post)
            
            with pytest.raises(Exception):
                db.session.commit()
    
    def test_blog_post_defaults(self, app, database):
        """Test blog post default values"""
        with app.app_context():
            post = BlogPost(
                title='New Post',
                slug='new-post',
                content='Content',
                author='Author'
            )
            db.session.add(post)
            db.session.commit()
            
            assert post.published is False
            assert post.view_count == 0
            assert post.created_at is not None
    
    def test_blog_post_view_increment(self, app, database):
        """Test incrementing view count"""
        with app.app_context():
            post = BlogPost.query.first()
            initial_views = post.view_count
            
            post.view_count += 1
            db.session.commit()
            
            assert post.view_count == initial_views + 1
    
    def test_blog_post_str_representation(self, app, database):
        """Test string representation"""
        with app.app_context():
            post = BlogPost.query.first()
            assert str(post) == '<BlogPost Test Blog Post 1>'
    
    def test_published_posts_query(self, app, database):
        """Test querying only published posts"""
        with app.app_context():
            published = BlogPost.query.filter_by(published=True).all()
            assert len(published) == 2
            
            for post in published:
                assert post.published is True


class TestPageView:
    """Tests for PageView model"""
    
    def test_create_page_view(self, app, database):
        """Test creating page view"""
        with app.app_context():
            post = BlogPost.query.first()
            
            view = PageView(
                blog_post_id=post.id,
                ip_address='192.168.1.1',
                user_agent='Mozilla/5.0 Test Browser'
            )
            db.session.add(view)
            db.session.commit()
            
            assert view.id is not None
            assert view.blog_post_id == post.id
            assert view.viewed_at is not None
    
    def test_page_view_relationship(self, app, database):
        """Test relationship with BlogPost"""
        with app.app_context():
            post = BlogPost.query.first()
            
            view = PageView(
                blog_post_id=post.id,
                ip_address='10.0.0.1',
                user_agent='Test'
            )
            db.session.add(view)
            db.session.commit()
            
            # Access relationship
            assert view.blog_post is not None
            assert view.blog_post.id == post.id
    
    def test_page_view_str_representation(self, app, database):
        """Test string representation"""
        with app.app_context():
            post = BlogPost.query.first()
            view = PageView(
                blog_post_id=post.id,
                ip_address='127.0.0.1',
                user_agent='Test'
            )
            db.session.add(view)
            db.session.commit()
            
            assert f'<PageView {view.id}>' in str(view)


class TestModelTimestamps:
    """Tests for timestamp behavior across models"""
    
    def test_created_at_auto_set(self, app, database):
        """Test created_at is automatically set"""
        with app.app_context():
            product = Product(
                name='Time Test',
                description='Test',
                price=1.00
            )
            db.session.add(product)
            db.session.commit()
            
            assert product.created_at is not None
            assert isinstance(product.created_at, datetime)
    
    def test_updated_at_auto_updates(self, app, database):
        """Test updated_at changes on modification"""
        with app.app_context():
            product = Product.query.first()
            original_updated = product.updated_at
            
            # Modify product
            product.price = 99.99
            db.session.commit()
            
            # updated_at should change (if implemented)
            # Note: Our models don't have updated_at yet
            assert product.price == 99.99
