"""
Coverage-focused tests for modular admin blog routes.

These tests target routes/admin/blog.py through app_factory.create_app().
"""

from __future__ import annotations

import pytest

from app_factory import create_app
from models import BlogPost, db


@pytest.fixture
def modular_app():
    app = create_app('testing')
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def modular_client(modular_app):
    return modular_app.test_client()


def login_session(client) -> None:
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True


def create_post(
    *,
    title: str,
    slug: str,
    content: str = 'content',
    author: str = 'Admin',
    published: bool = True,
    image_url: str = '/static/images/original.jpg',
) -> BlogPost:
    post = BlogPost(
        title=title,
        slug=slug,
        content=content,
        author=author,
        published=published,
        image_url=image_url,
        read_time='1 min',
    )
    db.session.add(post)
    db.session.commit()
    return post


def test_blog_list_requires_authentication(modular_client):
    response = modular_client.get('/admin/blog', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/login' in response.headers.get('Location', '')


def test_blog_list_renders_for_authenticated_admin(modular_client, modular_app):
    login_session(modular_client)

    with modular_app.app_context():
        create_post(title='Alpha', slug='alpha')

    response = modular_client.get('/admin/blog')
    assert response.status_code == 200
    assert b'Alpha' in response.data


def test_create_blog_get_renders_form(modular_client):
    login_session(modular_client)
    response = modular_client.get('/admin/blog/create')
    assert response.status_code == 200


def test_create_blog_post_defaults_to_published_without_control(modular_client, modular_app):
    login_session(modular_client)

    response = modular_client.post(
        '/admin/blog/create',
        data={
            'title': 'First Modular Post',
            'content': 'short content words',
            'author': 'Admin',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/admin/blog' in response.headers.get('Location', '')

    with modular_app.app_context():
        post = BlogPost.query.filter_by(title='First Modular Post').first()
        assert post is not None
        assert post.slug == 'first-modular-post'
        assert post.published is True
        assert post.image_url == '/static/images/placeholder.jpg'
        assert post.read_time == '1 min'


def test_create_blog_post_honors_unpublished_checkbox_state(modular_client, modular_app):
    login_session(modular_client)

    response = modular_client.post(
        '/admin/blog/create',
        data={
            'title': 'Draft Post',
            'content': 'draft body',
            'author': 'Admin',
            'published_present': '1',
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with modular_app.app_context():
        post = BlogPost.query.filter_by(title='Draft Post').first()
        assert post is not None
        assert post.published is False


def test_create_blog_post_resolves_duplicate_slugs_with_counter_loop(modular_client, modular_app):
    login_session(modular_client)

    with modular_app.app_context():
        create_post(title='Existing', slug='duplicate-title')
        create_post(title='Existing 2', slug='duplicate-title-1')

    response = modular_client.post(
        '/admin/blog/create',
        data={
            'title': 'Duplicate Title',
            'content': 'new content',
            'author': 'Admin',
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with modular_app.app_context():
        post = BlogPost.query.filter_by(title='Duplicate Title').first()
        assert post is not None
        assert post.slug == 'duplicate-title-2'


def test_edit_blog_get_404_for_missing_post(modular_client):
    login_session(modular_client)
    response = modular_client.get('/admin/blog/edit/999999')
    assert response.status_code == 404


def test_edit_blog_get_renders_existing_post(modular_client, modular_app):
    login_session(modular_client)

    with modular_app.app_context():
        post = create_post(title='Edit Form Post', slug='edit-form-post')
        post_id = post.id

    response = modular_client.get(f'/admin/blog/edit/{post_id}')
    assert response.status_code == 200
    assert b'Edit Form Post' in response.data


def test_edit_blog_post_updates_fields_and_unique_slug(modular_client, modular_app):
    login_session(modular_client)

    with modular_app.app_context():
        target = create_post(title='Target', slug='target-slug', content='old content')
        create_post(title='Conflict A', slug='new-slug')
        create_post(title='Conflict B', slug='new-slug-1')
        target_id = target.id

    response = modular_client.post(
        f'/admin/blog/edit/{target_id}',
        data={
            'title': 'Target Updated',
            'slug': 'new-slug',
            'content': 'updated content body',
            'excerpt': 'updated excerpt',
            'author': 'New Author',
            'category': 'Tech',
            'tags': 'python,flask',
            'published_present': '1',
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with modular_app.app_context():
        post = db.session.get(BlogPost, target_id)
        assert post is not None
        assert post.slug == 'new-slug-2'
        assert post.title == 'Target Updated'
        assert post.author == 'New Author'
        assert post.category == 'Tech'
        assert post.tags == 'python,flask'
        assert post.published is False
        assert post.image_url == '/static/images/original.jpg'


def test_edit_blog_without_published_control_keeps_existing_state(modular_client, modular_app):
    login_session(modular_client)

    with modular_app.app_context():
        post = create_post(title='Keep Publish', slug='keep-publish', published=True)
        post_id = post.id

    response = modular_client.post(
        f'/admin/blog/edit/{post_id}',
        data={
            'title': 'Keep Publish',
            'content': 'same slug path',
            'author': 'Admin',
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    with modular_app.app_context():
        updated = db.session.get(BlogPost, post_id)
        assert updated is not None
        assert updated.slug == 'keep-publish'
        assert updated.published is True


def test_delete_blog_post_success_and_missing_post(modular_client, modular_app):
    login_session(modular_client)

    with modular_app.app_context():
        post = create_post(title='Delete Me', slug='delete-me')
        post_id = post.id

    response = modular_client.post(f'/admin/blog/delete/{post_id}', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/blog' in response.headers.get('Location', '')

    with modular_app.app_context():
        assert db.session.get(BlogPost, post_id) is None

    missing = modular_client.post('/admin/blog/delete/999999')
    assert missing.status_code == 404
