"""
Coverage-focused tests for modular public routes.

These tests target routes/public.py through app_factory.create_app().
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.app_factory import create_app
from app.models import BlogPost, PageView, Product, Project, RaspberryPiProject, SiteConfig, db
from app.routes import public as public_routes


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


def test_index_renders_featured_projects_and_recent_posts(modular_client, modular_app):
    with modular_app.app_context():
        for idx in range(4):
            db.session.add(
                Project(
                    title=f'Featured {idx}',
                    description='Desc',
                    technologies='Python,Flask',
                    category='web',
                    featured=True,
                )
            )
        db.session.add(
            Project(
                title='Not Featured',
                description='Desc',
                technologies='Python',
                category='web',
                featured=False,
            )
        )
        db.session.add(
            BlogPost(
                title='Published Post',
                slug='published-post',
                excerpt='Excerpt',
                author='Tester',
                content='Body',
                category='Tech',
                published=True,
            )
        )
        db.session.add(
            BlogPost(
                title='Draft Post',
                slug='draft-post',
                excerpt='Excerpt',
                author='Tester',
                content='Body',
                category='Tech',
                published=False,
            )
        )
        db.session.commit()

    response = modular_client.get('/')
    assert response.status_code == 200
    body = response.data
    assert b'Featured 0' in body
    assert b'Published Post' in body
    assert b'Draft Post' not in body


def test_projects_page_lists_all_projects(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add_all(
            [
                Project(
                    title='Project A',
                    description='Desc',
                    technologies='Python',
                    category='web',
                ),
                Project(
                    title='Project B',
                    description='Desc',
                    technologies='Go',
                    category='backend',
                ),
            ]
        )
        db.session.commit()

    response = modular_client.get('/projects')
    assert response.status_code == 200
    assert b'Project A' in response.data
    assert b'Project B' in response.data


def test_project_detail_returns_200_and_404(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(
            Project(
                title='Detail Project',
                description='Detail description',
                technologies='Python,Flask',
                category='web',
            )
        )
        db.session.commit()
        project_id = Project.query.filter_by(title='Detail Project').first().id

    ok_response = modular_client.get(f'/projects/{project_id}')
    not_found_response = modular_client.get('/projects/99999')

    assert ok_response.status_code == 200
    assert b'Detail Project' in ok_response.data
    assert not_found_response.status_code == 404


def test_raspberry_pi_routes_render_and_404(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(
            RaspberryPiProject(
                title='RPi Build',
                description='Build details',
                hardware_json='["Pi 4"]',
                technologies='Python',
                features_json='["Monitoring"]',
            )
        )
        db.session.commit()
        rpi_id = RaspberryPiProject.query.first().id

    listing = modular_client.get('/raspberry-pi')
    resources = modular_client.get(f'/raspberry-pi/{rpi_id}/resources')
    missing = modular_client.get('/raspberry-pi/99999/resources')

    assert listing.status_code == 200
    assert b'RPi Build' in listing.data
    assert resources.status_code == 200
    assert missing.status_code == 404


def test_blog_listing_and_post_visibility(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add_all(
            [
                BlogPost(
                    title='Public Blog',
                    slug='public-blog',
                    excerpt='Excerpt',
                    author='Tester',
                    content='Body',
                    category='Tech',
                    published=True,
                ),
                BlogPost(
                    title='Hidden Blog',
                    slug='hidden-blog',
                    excerpt='Excerpt',
                    author='Tester',
                    content='Body',
                    category='Tech',
                    published=False,
                ),
            ]
        )
        db.session.commit()

    listing = modular_client.get('/blog')
    visible_post = modular_client.get('/blog/public-blog')
    hidden_post = modular_client.get('/blog/hidden-blog')

    assert listing.status_code == 200
    assert b'Public Blog' in listing.data
    assert b'Hidden Blog' not in listing.data
    assert visible_post.status_code == 200
    assert hidden_post.status_code == 404


def test_blog_post_tracks_analytics_and_increments_view_count(modular_client, modular_app, monkeypatch):
    with modular_app.app_context():
        db.session.add(
            SiteConfig(
                site_name='Test Site',
                blog_enabled=True,
                products_enabled=True,
                analytics_enabled=True,
            )
        )
        db.session.add(
            BlogPost(
                title='Tracked Post',
                slug='tracked-post',
                excerpt='Excerpt',
                author='Tester',
                content='Body',
                category='Tech',
                published=True,
                view_count=0,
            )
        )
        db.session.commit()

    captured_session_ids = []

    monkeypatch.setattr(
        public_routes,
        'parse_user_agent',
        lambda _ua: {'device_type': 'desktop', 'browser': 'TestBrowser', 'os': 'TestOS'},
    )
    monkeypatch.setattr(
        public_routes,
        'get_or_create_session',
        lambda session_id, _request: captured_session_ids.append(session_id),
    )

    response = modular_client.get('/blog/tracked-post')
    assert response.status_code == 200

    with modular_app.app_context():
        post = BlogPost.query.filter_by(slug='tracked-post').first()
        views = PageView.query.filter_by(path='/blog/tracked-post').all()
        assert post is not None
        assert post.view_count == 1
        assert len(views) == 1
        assert views[0].device_type == 'desktop'
        assert views[0].browser == 'TestBrowser'
        assert views[0].os == 'TestOS'

    assert len(captured_session_ids) == 1


def test_blog_post_handles_analytics_errors_without_failing_response(modular_client, modular_app, monkeypatch):
    with modular_app.app_context():
        db.session.add(
            SiteConfig(
                site_name='Test Site',
                blog_enabled=True,
                products_enabled=True,
                analytics_enabled=True,
            )
        )
        db.session.add(
            BlogPost(
                title='Rollback Post',
                slug='rollback-post',
                excerpt='Excerpt',
                author='Tester',
                content='Body',
                category='Tech',
                published=True,
                view_count=0,
            )
        )
        db.session.commit()

    monkeypatch.setattr(public_routes, 'parse_user_agent', lambda _ua: (_ for _ in ()).throw(RuntimeError('ua parse failed')))

    response = modular_client.get('/blog/rollback-post')
    assert response.status_code == 200

    with modular_app.app_context():
        post = BlogPost.query.filter_by(slug='rollback-post').first()
        views = PageView.query.filter_by(path='/blog/rollback-post').all()
        assert post is not None
        assert post.view_count == 0
        assert views == []


def test_products_about_and_contact_pages_render(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(
            Product(
                name='Test Product',
                description='Product description',
                price=19.99,
                type='digital',
                category='software',
            )
        )
        db.session.commit()

    products_response = modular_client.get('/products')
    about_response = modular_client.get('/about')
    contact_response = modular_client.get('/contact')

    assert products_response.status_code == 200
    assert b'Test Product' in products_response.data
    assert about_response.status_code == 200
    assert contact_response.status_code == 200
