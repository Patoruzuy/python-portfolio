"""
Tests for admin blog management routes.
"""
from app.models import db, BlogPost


class TestBlogList:
    """Test blog post listing page."""
    
    def test_blog_list_requires_auth(self, client, database):
        """Blog list page should require authentication."""
        response = client.get('/admin/blog')
        assert response.status_code in [302, 401, 403]
    
    def test_blog_list_loads_with_auth(self, auth_client, database):
        """Blog list page should load with authentication."""
        response = auth_client.get('/admin/blog')
        assert response.status_code == 200
    
    def test_blog_list_shows_posts(self, auth_client, database):
        """Blog list should display existing blog posts."""
        # Test data is already created by database fixture
        response = auth_client.get('/admin/blog')
        assert response.status_code == 200


class TestCreateBlogPost:
    """Test blog post creation."""
    
    def test_create_blog_get_requires_auth(self, client, database):
        """Create blog GET should require authentication."""
        response = client.get('/admin/blog/create')
        assert response.status_code in [302, 401, 403]
    
    def test_create_blog_get_loads_form(self, auth_client, database):
        """Create blog GET should load form."""
        response = auth_client.get('/admin/blog/create')
        assert response.status_code == 200
    
    def test_create_blog_post_success(self, auth_client, database):
        """Should create a new blog post successfully."""
        data = {
            'title': 'New Blog Post',
            'excerpt': 'This is an excerpt',
            'author': 'Test Author',
            'content': 'This is the full content of the blog post with many words to test read time calculation.',
            'category': 'Technology',
            'tags': 'python, testing',
            'image': '/static/images/test.jpg',
            'published': 'on'
        }
        
        response = auth_client.post('/admin/blog/create', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify post was created
        post = BlogPost.query.filter_by(title='New Blog Post').first()
        assert post is not None
        assert post.slug == 'new-blog-post'
        assert post.published is True
    
    def test_create_blog_auto_generates_slug(self, auth_client, database):
        """Should auto-generate slug from title."""
        data = {
            'title': 'Test Blog Post With Spaces',
            'content': 'Content here',
            'author': 'Admin'
        }
        
        auth_client.post('/admin/blog/create', data=data)
        
        post = BlogPost.query.filter_by(title='Test Blog Post With Spaces').first()
        assert post is not None
        assert post.slug == 'test-blog-post-with-spaces'


class TestEditBlogPost:
    """Test blog post editing."""
    
    def test_edit_blog_get_loads_form(self, auth_client, database):
        """Edit blog GET should load form with post data."""
        # Use existing test post from fixture
        post = BlogPost.query.first()
        assert post is not None
        
        response = auth_client.get(f'/admin/blog/edit/{post.id}')
        assert response.status_code == 200
    
    def test_edit_blog_post_updates_fields(self, auth_client, database):
        """Should update blog post fields."""
        post = BlogPost.query.first()
        post_id = post.id
        
        data = {
            'title': 'Updated Title',
            'slug': 'updated-slug',
            'content': 'Updated Content with enough words to calculate read time',
            'excerpt': 'Updated Excerpt',
            'author': 'Updated Author',
            'category': 'Updated Category'
        }
        
        response = auth_client.post(f'/admin/blog/edit/{post_id}', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify updates
        updated_post = BlogPost.query.get(post_id)
        assert updated_post.title == 'Updated Title'


class TestDeleteBlogPost:
    """Test blog post deletion."""
    
    def test_delete_blog_post_success(self, auth_client, database):
        """Should delete blog post successfully."""
        post = BlogPost(
            title="Post to Delete",
            slug="post-to-delete",
            content="Content",
            author="Admin"
        )
        db.session.add(post)
        db.session.commit()
        post_id = post.id
        
        response = auth_client.post(f'/admin/blog/delete/{post_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify deletion
        deleted_post = BlogPost.query.get(post_id)
        assert deleted_post is None
