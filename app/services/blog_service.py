"""
Blog service layer.
Handles all blog-related business logic and data operations.
"""
from app.models import db, BlogPost
from app.services import BaseService, cache_result, invalidate_cache_pattern
from typing import List, Optional, Dict, Any
from slugify import slugify
from sqlalchemy import or_


class BlogService(BaseService):
    """Service for blog operations."""
    
    @cache_result(timeout=600, key_prefix='blog:all')
    def get_all_published(self, limit: Optional[int] = None) -> List[BlogPost]:
        """
        Get all published blog posts.
        
        Args:
            limit: Optional limit for number of posts
            
        Returns:
            List of published blog posts
        """
        query = BlogPost.query.filter_by(published=True).order_by(
            BlogPost.created_at.desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @cache_result(timeout=600, key_prefix='blog:post')
    def get_by_slug(self, slug: str) -> Optional[BlogPost]:
        """
        Get blog post by slug.
        
        Args:
            slug: Post slug
            
        Returns:
            BlogPost or None
        """
        return BlogPost.query.filter_by(slug=slug, published=True).first()
    
    @cache_result(timeout=600, key_prefix='blog:category')
    def get_by_category(self, category: str) -> List[BlogPost]:
        """
        Get blog posts by category.
        
        Args:
            category: Category name
            
        Returns:
            List of blog posts in category
        """
        return BlogPost.query.filter_by(
            published=True,
            category=category
        ).order_by(BlogPost.created_at.desc()).all()
    
    @cache_result(timeout=600, key_prefix='blog:tag')
    def get_by_tag(self, tag: str) -> List[BlogPost]:
        """
        Get blog posts by tag.
        
        Args:
            tag: Tag name
            
        Returns:
            List of blog posts with tag
        """
        return BlogPost.query.filter(
            BlogPost.published == True,  # noqa: E712
            BlogPost.tags.contains(tag)
        ).order_by(BlogPost.created_at.desc()).all()
    
    @cache_result(timeout=600, key_prefix='blog:search')
    def search(self, query: str) -> List[BlogPost]:
        """
        Search blog posts by title, excerpt, or content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching blog posts
        """
        search_pattern = f"%{query}%"
        return BlogPost.query.filter(
            BlogPost.published == True,  # noqa: E712
            or_(
                BlogPost.title.ilike(search_pattern),
                BlogPost.excerpt.ilike(search_pattern),
                BlogPost.content.ilike(search_pattern)
            )
        ).order_by(BlogPost.created_at.desc()).all()
    
    def create_post(self, data: Dict[str, Any]) -> BlogPost:
        """
        Create new blog post.
        
        Args:
            data: Post data dictionary
            
        Returns:
            Created BlogPost
        """
        # Generate slug if not provided
        if not data.get('slug'):
            data['slug'] = slugify(data['title'])
        
        post = BlogPost(**data)
        db.session.add(post)
        db.session.commit()
        
        # Invalidate blog cache
        self._invalidate_blog_cache()
        
        return post
    
    def update_post(self, post_id: int, data: Dict[str, Any]) -> Optional[BlogPost]:
        """
        Update blog post.
        
        Args:
            post_id: Post ID
            data: Updated post data
            
        Returns:
            Updated BlogPost or None
        """
        post = BlogPost.query.get(post_id)
        if not post:
            return None
        
        # Update fields
        for key, value in data.items():
            if hasattr(post, key):
                setattr(post, key, value)
        
        # Update slug if title changed
        if 'title' in data and not data.get('slug'):
            post.slug = slugify(data['title'])
        
        db.session.commit()
        
        # Invalidate blog cache
        self._invalidate_blog_cache()
        
        return post
    
    def delete_post(self, post_id: int) -> bool:
        """
        Delete blog post.
        
        Args:
            post_id: Post ID
            
        Returns:
            True if deleted, False otherwise
        """
        post = BlogPost.query.get(post_id)
        if not post:
            return False
        
        db.session.delete(post)
        db.session.commit()
        
        # Invalidate blog cache
        self._invalidate_blog_cache()
        
        return True
    
    def increment_view_count(self, post_id: int) -> bool:
        """
        Increment view count for blog post.
        
        Args:
            post_id: Post ID
            
        Returns:
            True if successful
        """
        post = BlogPost.query.get(post_id)
        if not post:
            return False
        
        post.view_count += 1
        db.session.commit()
        
        return True
    
    def _invalidate_blog_cache(self) -> None:
        """Invalidate all blog-related cache entries."""
        patterns = ['blog:all', 'blog:post', 'blog:category', 'blog:tag', 'blog:search']
        for pattern in patterns:
            invalidate_cache_pattern(pattern)


# Global instance
blog_service = BlogService()
