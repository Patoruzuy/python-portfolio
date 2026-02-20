"""
Additional tests for admin blog POST operations.
"""
import pytest
from models import db, BlogPost
from datetime import datetime


class TestBlogCreate:
    """Test blog post creation."""
    
    def test_create_blog_post_success(self, auth_client, database):
        """Should create blog post successfully."""
        response = auth_client.post('/admin/blog/create', data={
            'title': 'New Test Blog Post',
            'content': 'This is test content for the blog post.',
            'excerpt': 'Test excerpt',
            'author': 'Test Author',
            'tags': 'python,testing',
            'category': 'tutorial',
            'published': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Verify post was created
        post = BlogPost.query.filter_by(title='New Test Blog Post').first()
        assert post is not None
        assert post.content == 'This is test content for the blog post.'
        assert post.published is True
    
    def test_create_blog_post_generates_slug(self, auth_client, database):
        """Should auto-generate slug from title."""
        response = auth_client.post('/admin/blog/create', data={
            'title': 'Test Blog Post Title',
            'content': 'Content here',
            'author': 'Test Author',
            'published': 'on'
        }, follow_redirects=True)
        
        post = BlogPost.query.filter_by(title='Test Blog Post Title').first()
        assert post is not None
        assert post.slug == 'test-blog-post-title'
    
    def test_create_blog_post_handles_duplicate_slug(self, auth_client, database):
        """Should handle duplicate slugs by appending counter."""
        # Create first post
        auth_client.post('/admin/blog/create', data={
            'title': 'Duplicate Title',
            'content': 'First post',
            'author': 'Test Author',
            'published': 'on'
        })
        
        # Create second post with same title
        auth_client.post('/admin/blog/create', data={
            'title': 'Duplicate Title',
            'content': 'Second post',
            'author': 'Test Author',
            'published': 'on'
        })
        
        posts = BlogPost.query.filter(BlogPost.slug.like('duplicate-title%')).all()
        assert len(posts) == 2
        assert posts[0].slug == 'duplicate-title'
        assert posts[1].slug == 'duplicate-title-1'
    
    def test_create_blog_post_calculates_read_time(self, auth_client, database):
        """Should calculate read time based on content."""
        # Create post with ~200 words (should be 1 min)
        content = ' '.join(['word'] * 200)
        auth_client.post('/admin/blog/create', data={
            'title': 'Read Time Test',
            'content': content,
            'author': 'Test Author',
            'published': 'on'
        })
        
        post = BlogPost.query.filter_by(title='Read Time Test').first()
        assert post.read_time == '1 min'
    
    def test_create_blog_post_unpublished(self, auth_client, database):
        """Should create unpublished draft post."""
        response = auth_client.post('/admin/blog/create', data={
            'title': 'Draft Post',
            'content': 'Draft content',
            'author': 'Test Author',
            'published_present': '1'
            # No 'published' checkbox checked
        }, follow_redirects=True)
        
        post = BlogPost.query.filter_by(title='Draft Post').first()
        assert post is not None
        assert post.published is False


class TestBlogUpdate:
    """Test blog post updating."""
    
    def test_update_blog_post_success(self, auth_client, database):
        """Should update existing blog post."""
        # Create initial post
        post = BlogPost(
            title='Original Title',
            slug='original-title',
            content='Original content',
            author='Test Author',
            published=True
        )
        db.session.add(post)
        db.session.commit()
        post_id = post.id
        
        # Update post
        response = auth_client.post(f'/admin/blog/edit/{post_id}', data={
            'title': 'Updated Title',
            'content': 'Updated content',
            'excerpt': 'New excerpt',
            'author': 'Test Author',
            'published': 'on'
        }, follow_redirects=True)
        
        updated_post = BlogPost.query.get(post_id)
        assert updated_post.title == 'Updated Title'
        assert updated_post.content == 'Updated content'
    
    def test_update_blog_post_regenerates_slug(self, auth_client, database):
        """Should regenerate slug when title changes."""
        post = BlogPost(
            title='Old Title',
            slug='old-title',
            content='Content',
            author='Test Author',
            published=True
        )
        db.session.add(post)
        db.session.commit()
        post_id = post.id
        
        auth_client.post(f'/admin/blog/edit/{post_id}', data={
            'title': 'Brand New Title',
            'content': 'Content',
            'author': 'Test Author',
            'published': 'on'
        })
        
        updated_post = BlogPost.query.get(post_id)
        assert updated_post.slug == 'brand-new-title'
    
    def test_update_blog_post_to_unpublished(self, auth_client, database):
        """Should update published post to unpublished."""
        post = BlogPost(
            title='Published Post',
            slug='published-post',
            content='Content',
            author='Test Author',
            published=True
        )
        db.session.add(post)
        db.session.commit()
        post_id = post.id
        
        auth_client.post(f'/admin/blog/edit/{post_id}', data={
            'title': 'Published Post',
            'content': 'Content',
            'author': 'Test Author',
            'published_present': '1'
            # No 'published' checkbox
        })
        
        updated_post = BlogPost.query.get(post_id)
        assert updated_post.published is False


class TestBlogDelete:
    """Test blog post deletion."""
    
    def test_delete_blog_post_success(self, auth_client, database):
        """Should delete blog post."""
        post = BlogPost(
            title='To Delete',
            slug='to-delete',
            content='Will be deleted',
            author='Test Author',
            published=True
        )
        db.session.add(post)
        db.session.commit()
        post_id = post.id
        
        response = auth_client.post(f'/admin/blog/delete/{post_id}', follow_redirects=True)
        
        assert response.status_code == 200
        deleted_post = BlogPost.query.get(post_id)
        assert deleted_post is None
    
    def test_delete_nonexistent_blog_post(self, auth_client, database):
        """Should handle deleting nonexistent post."""
        response = auth_client.post('/admin/blog/delete/99999', follow_redirects=True)
        # Should redirect or show error, not crash
        assert response.status_code in [200, 404]


class TestBlogFormValidation:
    """Test blog form validation."""
    
    def test_create_blog_post_handles_empty_content(self, auth_client, database):
        """Should handle empty content."""
        response = auth_client.post('/admin/blog/create', data={
            'title': 'Title Only Post',
            'content': '',
            'author': 'Test Author',
            'published': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        post = BlogPost.query.filter_by(title='Title Only Post').first()
        assert post is not None
