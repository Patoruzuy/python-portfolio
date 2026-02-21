"""
Tests for blog service layer.
Comprehensive testing of all blog-related business logic.
"""
import pytest
from unittest.mock import patch
from app.models import db, BlogPost
from app.services.blog_service import BlogService
from datetime import datetime, timedelta


# Mock the cache_result decorator to pass through without caching
def passthrough_decorator(*args, **kwargs):
    """Decorator that does nothing - just returns the function."""
    def decorator(f):
        return f
    return decorator


@pytest.fixture(autouse=True)
def disable_caching():
    """Disable caching for all blog service tests."""
    with patch('app.services.cache_result', passthrough_decorator):
        with patch('app.services.invalidate_cache_pattern'):
            yield


class TestBlogService:
    """Test suite for BlogService class."""
    
    @pytest.fixture
    def blog_service(self):
        """Create blog service instance."""
        return BlogService()
    
    @pytest.fixture
    def sample_posts(self, database):
        """Create sample blog posts for testing."""
        posts = [
            BlogPost(
                title='First Post',
                slug='first-post',
                content='Content for first post',
                excerpt='Excerpt 1',
                author='Test Author',
                published=True,
                category='Tech',
                tags='python,flask',
                created_at=datetime.utcnow()
            ),
            BlogPost(
                title='Second Post',
                slug='second-post',
                content='Content for second post',
                excerpt='Excerpt 2',
                author='Test Author',
                published=True,
                category='Tutorial',
                tags='python,testing',
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            BlogPost(
                title='Unpublished Post',
                slug='unpublished-post',
                content='Draft content',
                excerpt='Draft excerpt',
                author='Test Author',
                published=False,
                category='Tech',
                tags='draft',
                created_at=datetime.utcnow() - timedelta(days=2)
            ),
            BlogPost(
                title='Another Tech Post',
                slug='another-tech-post',
                content='More tech content about Python and databases',
                excerpt='Tech excerpt',
                author='Test Author',
                published=True,
                category='Tech',
                tags='python,database',
                created_at=datetime.utcnow() - timedelta(days=3)
            ),
        ]
        
        for post in posts:
            db.session.add(post)
        db.session.commit()
        
        return posts
    
    # Test: Get all published posts
    def test_get_all_published_returns_only_published(
        self,
        blog_service,
        sample_posts
    ):
        """Test that get_all_published returns only published posts."""
        posts = blog_service.get_all_published()
        
        # Should have at least our 3 published sample posts (plus any from database fixture)
        assert len(posts) >= 3
        assert all(post.published for post in posts)
        assert 'Unpublished Post' not in [p.title for p in posts]
        # Verify our sample posts are present
        titles = [p.title for p in posts]
        assert 'First Post' in titles
        assert 'Second Post' in titles
        assert 'Another Tech Post' in titles
    
    def test_get_all_published_orders_by_created_desc(
        self,
        blog_service,
        sample_posts
    ):
        """Test that posts are ordered by created date descending."""
        posts = blog_service.get_all_published()
        
        # Verify posts are ordered by created_at descending
        assert len(posts) >= 2
        for i in range(len(posts) - 1):
            assert posts[i].created_at >= posts[i + 1].created_at
    
    def test_get_all_published_with_limit(
        self,
        blog_service,
        sample_posts
    ):
        """Test that limit parameter works correctly."""
        posts = blog_service.get_all_published(limit=2)
        
        # Should return exactly 2 posts (the limit)
        assert len(posts) == 2
        # Should still be ordered by created_at descending
        assert posts[0].created_at >= posts[1].created_at
    
    def test_get_all_published_empty_database(
        self,
        blog_service,
        database
    ):
        """Test get_all_published with no posts in database."""
        # Clear any existing posts from database fixture
        from app.models import BlogPost
        from app import db
        BlogPost.query.delete()
        db.session.commit()
        
        posts = blog_service.get_all_published()
        
        assert posts == []
    
    # Test: Get post by slug
    def test_get_by_slug_success(
        self,
        blog_service,
        sample_posts
    ):
        """Test successfully getting post by slug."""
        post = blog_service.get_by_slug('first-post')
        
        assert post is not None
        assert post.title == 'First Post'
        assert post.slug == 'first-post'
    
    def test_get_by_slug_unpublished_returns_none(
        self,
        blog_service,
        sample_posts
    ):
        """Test that unpublished posts are not returned."""
        post = blog_service.get_by_slug('unpublished-post')
        
        assert post is None
    
    def test_get_by_slug_nonexistent_returns_none(
        self,
        blog_service,
        sample_posts
    ):
        """Test getting nonexistent post returns None."""
        post = blog_service.get_by_slug('nonexistent-slug')
        
        assert post is None
    
    # Test: Get posts by category
    def test_get_by_category_success(
        self,
        blog_service,
        sample_posts
    ):
        """Test getting posts by category."""
        posts = blog_service.get_by_category('Tech')
        
        assert len(posts) == 2
        assert all(post.category == 'Tech' for post in posts)
        assert posts[0].title == 'First Post'
    
    def test_get_by_category_no_results(
        self,
        blog_service,
        sample_posts
    ):
        """Test getting posts from nonexistent category."""
        posts = blog_service.get_by_category('Nonexistent')
        
        assert posts == []
    
    def test_get_by_category_excludes_unpublished(
        self,
        blog_service,
        sample_posts
    ):
        """Test that category filter excludes unpublished posts."""
        posts = blog_service.get_by_category('Tech')
        
        assert all(post.published for post in posts)
        assert 'Unpublished Post' not in [p.title for p in posts]
    
    # Test: Get posts by tag
    def test_get_by_tag_success(
        self,
        blog_service,
        sample_posts
    ):
        """Test getting posts by tag."""
        posts = blog_service.get_by_tag('python')
        
        # Should have at least 2 posts with 'python' tag from sample_posts
        assert len(posts) >= 2
        assert all('python' in post.tags.lower() for post in posts)
        # Verify our sample posts are present
        titles = [p.title for p in posts]
        assert 'First Post' in titles
        assert 'Second Post' in titles
    
    def test_get_by_tag_single_result(
        self,
        blog_service,
        sample_posts
    ):
        """Test getting posts with unique tag."""
        posts = blog_service.get_by_tag('database')
        
        assert len(posts) == 1
        assert posts[0].title == 'Another Tech Post'
    
    def test_get_by_tag_no_results(
        self,
        blog_service,
        sample_posts
    ):
        """Test getting posts with nonexistent tag."""
        posts = blog_service.get_by_tag('nonexistent')
        
        assert posts == []
    
    # Test: Search posts
    def test_search_by_title(
        self,
        blog_service,
        sample_posts
    ):
        """Test searching posts by title."""
        posts = blog_service.search('First')
        
        assert len(posts) == 1
        assert posts[0].title == 'First Post'
    
    def test_search_by_content(
        self,
        blog_service,
        sample_posts
    ):
        """Test searching posts by content."""
        posts = blog_service.search('databases')
        
        assert len(posts) == 1
        assert posts[0].title == 'Another Tech Post'
    
    def test_search_by_excerpt(
        self,
        blog_service,
        sample_posts
    ):
        """Test searching posts by excerpt."""
        posts = blog_service.search('Tech excerpt')
        
        assert len(posts) == 1
        assert posts[0].title == 'Another Tech Post'
    
    def test_search_case_insensitive(
        self,
        blog_service,
        sample_posts
    ):
        """Test that search is case insensitive."""
        posts_lower = blog_service.search('tech')
        posts_upper = blog_service.search('TECH')
        
        assert len(posts_lower) == len(posts_upper)
        assert len(posts_lower) > 0
    
    def test_search_multiple_results(
        self,
        blog_service,
        sample_posts
    ):
        """Test search returning multiple results."""
        # Search for 'content' which appears in multiple post contents
        posts = blog_service.search('content')
        
        # Should find multiple posts with 'content' in title/content/excerpt
        assert len(posts) >= 2
    
    def test_search_no_results(
        self,
        blog_service,
        sample_posts
    ):
        """Test search with no matching results."""
        posts = blog_service.search('nonexistent-term-xyz')
        
        assert posts == []
    
    def test_search_excludes_unpublished(
        self,
        blog_service,
        sample_posts
    ):
        """Test that search excludes unpublished posts."""
        posts = blog_service.search('Draft')
        
        assert posts == []
    
    # Test: Create post
    def test_create_post_success(
        self,
        blog_service,
        database
    ):
        """Test creating a new blog post."""
        data = {
            'title': 'New Post',
            'content': 'New content',
            'excerpt': 'New excerpt',
            'author': 'Test Author',
            'category': 'Tech',
            'tags': 'python',
            'published': True
        }
        
        post = blog_service.create_post(data)
        
        assert post.title == 'New Post'
        assert post.slug == 'new-post'
        assert post.published is True
        
        # Verify it's in database
        db_post = BlogPost.query.filter_by(slug='new-post').first()
        assert db_post is not None
        assert db_post.title == 'New Post'
    
    def test_create_post_auto_generates_slug(
        self,
        blog_service,
        database
    ):
        """Test that slug is auto-generated from title."""
        data = {
            'title': 'My Amazing Post!',
            'author': 'Test Author',
            'content': 'Content',
            'published': False
        }
        
        post = blog_service.create_post(data)
        
        assert post.slug == 'my-amazing-post'
    
    def test_create_post_with_custom_slug(
        self,
        blog_service,
        database
    ):
        """Test creating post with custom slug."""
        data = {
            'title': 'My Post',
            'slug': 'custom-slug',
            'author': 'Test Author',
            'content': 'Content',
            'published': False
        }
        
        post = blog_service.create_post(data)
        
        assert post.slug == 'custom-slug'
    
    # Test: Update post
    def test_update_post_success(
        self,
        blog_service,
        sample_posts
    ):
        """Test updating an existing post."""
        post = sample_posts[0]
        updates = {
            'title': 'Updated Title',
            'content': 'Updated content'
        }
        
        updated = blog_service.update_post(post.id, updates)
        
        assert updated.title == 'Updated Title'
        assert updated.content == 'Updated content'
        # Slug is auto-generated from the new title when title changes
        assert updated.slug == 'updated-title'
    
    def test_update_post_change_slug(
        self,
        blog_service,
        sample_posts
    ):
        """Test updating post slug."""
        post = sample_posts[0]
        updates = {'slug': 'new-slug'}
        
        updated = blog_service.update_post(post.id, updates)
        
        assert updated.slug == 'new-slug'
    
    def test_update_post_publish_toggle(
        self,
        blog_service,
        sample_posts
    ):
        """Test toggling post published status."""
        post = sample_posts[2]  # Unpublished post
        assert post.published is False
        
        updated = blog_service.update_post(post.id, {'published': True})
        
        assert updated.published is True
    
    def test_update_nonexistent_post(
        self,
        blog_service,
        database
    ):
        """Test updating nonexistent post returns None."""
        updated = blog_service.update_post(99999, {'title': 'Test'})
        
        assert updated is None
    
    # Test: Delete post
    def test_delete_post_success(
        self,
        blog_service,
        sample_posts
    ):
        """Test deleting a post."""
        post = sample_posts[0]
        post_id = post.id
        
        result = blog_service.delete_post(post_id)
        
        assert result is True
        
        # Verify it's deleted
        deleted_post = BlogPost.query.get(post_id)
        assert deleted_post is None
    
    def test_delete_nonexistent_post(
        self,
        blog_service,
        database
    ):
        """Test deleting nonexistent post returns False."""
        result = blog_service.delete_post(99999)
        
        assert result is False
    
    # Test: Get by ID - BlogService doesn't have get_by_id, it queries directly
    # These tests are removed as the method doesn't exist in the service
    
    # Test: Increment views
    def test_increment_view_count(
        self,
        blog_service,
        sample_posts
    ):
        """Test incrementing post view count."""
        post = sample_posts[0]
        initial_views = post.view_count or 0
        
        result = blog_service.increment_view_count(post.id)
        
        assert result is True
        db.session.refresh(post)
        assert post.view_count == initial_views + 1
    
    def test_increment_view_count_multiple_times(
        self,
        blog_service,
        sample_posts
    ):
        """Test incrementing views multiple times."""
        post = sample_posts[0]
        initial_views = post.view_count or 0
        
        for _ in range(5):
            blog_service.increment_view_count(post.id)
        
        db.session.refresh(post)
        assert post.view_count == initial_views + 5
    
    # Test: Get statistics - Method doesn't exist in service, removing tests
