"""
Admin blog management routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.wrappers.response import Response as WerkzeugResponse
from slugify import slugify
from typing import Union
from models import db, BlogPost
from routes.admin.utils import login_required, is_truthy

# Create admin blog blueprint
admin_blog_bp = Blueprint('admin_blog', __name__, url_prefix='/admin')


@admin_blog_bp.route('/blog')
@login_required
def blog() -> str:
    """List all blog posts."""
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


@admin_blog_bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog_post() -> Union[str, WerkzeugResponse]:
    """Create a new blog post."""
    if request.method == 'POST':
        title = request.form.get('title') or ''

        # Auto-generate slug from title
        slug = slugify(title) if title else ''

        # Ensure slug is unique
        existing = BlogPost.query.filter_by(slug=slug).first()
        if existing:
            counter = 1
            while BlogPost.query.filter_by(slug=f"{slug}-{counter}").first():
                counter += 1
            slug = f"{slug}-{counter}"

        # Calculate read time (200 words per minute)
        content = request.form.get('content', '')
        word_count = len(content.split())
        read_time = f"{max(1, round(word_count / 200))} min"

        has_published_control = request.form.get('published_present') == '1'
        published = is_truthy(request.form.get('published')) if has_published_control else True

        post = BlogPost(
            title=title,
            slug=slug,
            excerpt=request.form.get('excerpt'),
            author=request.form.get('author', 'Admin'),
            content=content,
            category=request.form.get('category', 'Uncategorized'),
            tags=request.form.get('tags', ''),
            image_url=request.form.get('image') or '/static/images/placeholder.jpg',
            read_time=read_time,
            published=published
        )

        db.session.add(post)
        db.session.commit()

        flash(f'Blog post created successfully! Slug: {slug}', 'success')
        return redirect(url_for('admin_blog.blog'))

    return render_template('admin/blog_form.html', post=None)


@admin_blog_bp.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_blog_post(post_id: int) -> Union[str, WerkzeugResponse]:
    """Edit an existing blog post."""
    post = BlogPost.query.get_or_404(post_id)

    if request.method == 'POST':
        title = request.form.get('title') or ''
        new_slug = request.form.get('slug') or (slugify(title) if title else '')

        # Ensure slug is unique (excluding current post)
        if new_slug != post.slug:
            existing = BlogPost.query.filter(
                BlogPost.slug == new_slug,
                BlogPost.id != post_id).first()
            if existing:
                counter = 1
                while BlogPost.query.filter(
                        BlogPost.slug == f"{new_slug}-{counter}",
                        BlogPost.id != post_id).first():
                    counter += 1
                new_slug = f"{new_slug}-{counter}"

        # Recalculate read time if content changed
        content = request.form.get('content', '')
        word_count = len(content.split())
        read_time = f"{max(1, round(word_count / 200))} min"

        post.title = title
        post.slug = new_slug
        post.excerpt = request.form.get('excerpt')
        post.author = request.form.get('author')
        post.content = content
        post.category = request.form.get('category')
        post.tags = request.form.get('tags', '')
        post.image_url = request.form.get('image') or post.image_url
        post.read_time = read_time
        has_published_control = request.form.get('published_present') == '1'
        if has_published_control:
            post.published = is_truthy(request.form.get('published'))

        db.session.commit()

        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin_blog.blog'))

    return render_template('admin/blog_form.html', post=post)


@admin_blog_bp.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_blog_post(post_id: int) -> WerkzeugResponse:
    """Delete a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('admin_blog.blog'))
