"""
Coverage-focused tests for modular admin settings routes.

These tests target routes/admin/settings.py directly via app_factory.create_app(),
because the legacy app.py stack uses admin_routes.py instead.
"""

from __future__ import annotations

import builtins
import json

import pytest

from app.app_factory import create_app
from app.models import db, OwnerProfile, SiteConfig


@pytest.fixture
def modular_app():
    """Create a factory-based app instance with isolated in-memory DB."""
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


def login_admin(client) -> None:
    """Set authenticated admin session for routes guarded by login_required."""
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True


def test_owner_profile_creates_default_when_missing(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        OwnerProfile.query.delete()
        db.session.commit()

    response = modular_client.get('/admin/owner-profile')
    assert response.status_code == 200

    with modular_app.app_context():
        owner = OwnerProfile.query.first()
        assert owner is not None
        assert owner.name == 'Portfolio Owner'
        assert owner.email == 'contact@example.com'


def test_owner_profile_invalid_numeric_value_returns_form(modular_client, modular_app):
    login_admin(modular_client)

    response = modular_client.post('/admin/owner-profile', data={
        'name': 'Test',
        'title': 'Engineer',
        'email': 'test@example.com',
        'years_experience': 'invalid-number',
        'skills_json': '[]',
        'experience_json': '[]',
        'expertise_json': '[]',
    })

    assert response.status_code == 200
    assert b'Owner Profile' in response.data

    with modular_app.app_context():
        # Invalid numeric input should not persist partial owner changes.
        owner = OwnerProfile.query.first()
        assert owner is not None
        assert owner.name == 'Portfolio Owner'
        assert owner.years_experience == 0


def test_owner_profile_invalid_json_returns_form(modular_client, modular_app):
    login_admin(modular_client)

    response = modular_client.post('/admin/owner-profile', data={
        'name': 'Test',
        'title': 'Engineer',
        'email': 'test@example.com',
        'years_experience': '1',
        'projects_completed': '2',
        'contributions': '3',
        'clients_served': '4',
        'certifications': '5',
        'skills_json': '{bad json}',
        'experience_json': '[]',
        'expertise_json': '[]',
    })

    assert response.status_code == 200
    assert b'Owner Profile' in response.data

    with modular_app.app_context():
        # Invalid JSON should not persist partial owner changes.
        owner = OwnerProfile.query.first()
        assert owner is not None
        assert owner.name == 'Portfolio Owner'
        assert owner.skills_json == '[]'


def test_owner_profile_keeps_existing_image_when_field_empty(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        owner = OwnerProfile(
            name='Existing',
            title='Dev',
            email='existing@example.com',
            profile_image='/static/images/existing.png',
        )
        db.session.add(owner)
        db.session.commit()

    response = modular_client.post('/admin/owner-profile', data={
        'name': 'Existing',
        'title': 'Dev',
        'email': 'existing@example.com',
        'profile_image': '',
        'years_experience': '1',
        'projects_completed': '1',
        'contributions': '1',
        'clients_served': '1',
        'certifications': '1',
        'skills_json': '[]',
        'experience_json': '[]',
        'expertise_json': '[]',
    }, follow_redirects=False)

    assert response.status_code == 302

    with modular_app.app_context():
        owner = OwnerProfile.query.first()
        assert owner.profile_image == '/static/images/existing.png'


def test_site_config_creates_default_when_missing(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        SiteConfig.query.delete()
        db.session.commit()

    response = modular_client.get('/admin/site-config')
    assert response.status_code == 200

    with modular_app.app_context():
        config = SiteConfig.query.first()
        assert config is not None
        assert config.site_name == 'Developer Portfolio'
        assert config.blog_enabled is True
        assert config.products_enabled is True


def test_site_config_invalid_mail_port_defaults_to_587(modular_client, modular_app):
    login_admin(modular_client)

    response = modular_client.post('/admin/site-config', data={
        'site_name': 'Config Test',
        'mail_port': 'not-a-number',
    }, follow_redirects=False)

    assert response.status_code == 302

    with modular_app.app_context():
        config = SiteConfig.query.first()
        assert config.mail_port == 587


def test_site_config_import_error_path_still_succeeds(modular_client, modular_app, monkeypatch):
    login_admin(modular_client)

    original_import = builtins.__import__

    def import_with_app_failure(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'app':
            raise ImportError('simulated import error for tests')
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, '__import__', import_with_app_failure)

    response = modular_client.post('/admin/site-config', data={
        'site_name': 'No App Import',
        'mail_port': '587',
    }, follow_redirects=False)

    assert response.status_code == 302
    assert '/admin/site-config' in response.headers.get('Location', '')

    with modular_app.app_context():
        config = SiteConfig.query.first()
        assert config is not None
        assert config.site_name == 'No App Import'


def test_export_config_handles_missing_records(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        OwnerProfile.query.delete()
        SiteConfig.query.delete()
        db.session.commit()

    response = modular_client.get('/admin/export-config')
    assert response.status_code == 200
    data = response.get_json()
    assert data['owner_profile']['name'] is None
    assert data['site_config']['site_name'] is None
    assert data['site_config']['blog_enabled'] is True


def test_import_config_rejects_missing_form_payload(modular_client):
    login_admin(modular_client)

    response = modular_client.post('/admin/import-config', data={})
    assert response.status_code == 400
    assert response.get_json()['success'] is False


def test_import_config_rejects_invalid_form_json(modular_client):
    login_admin(modular_client)

    response = modular_client.post('/admin/import-config', data={
        'config_data': '{not-valid-json}'
    })
    assert response.status_code == 400
    assert response.get_json()['success'] is False


def test_import_config_creates_owner_and_site_from_json(modular_client, modular_app):
    login_admin(modular_client)

    payload = {
        'owner_profile': {
            'name': 'Imported Owner',
            'title': 'Architect',
            'email': 'imported@example.com',
            'years_experience': 9,
            'projects_completed': 50,
            'contributions': 500,
            'clients_served': 20,
            'certifications': 4,
            'skills': ['Python', 'Flask'],
            'experience': [{'company': 'Acme'}],
            'expertise': [{'domain': 'Security'}],
        },
        'site_config': {
            'site_name': 'Imported Site',
            'tagline': 'Imported Tagline',
            'mail_server': 'smtp.example.com',
            'mail_port': 2525,
            'mail_use_tls': True,
            'blog_enabled': False,
            'products_enabled': True,
            'analytics_enabled': True,
        },
    }

    response = modular_client.post('/admin/import-config', json=payload)
    assert response.status_code == 200
    assert response.get_json()['success'] is True

    with modular_app.app_context():
        owner = OwnerProfile.query.first()
        config = SiteConfig.query.first()
        assert owner is not None
        assert config is not None
        assert owner.name == 'Imported Owner'
        assert json.loads(owner.skills_json) == ['Python', 'Flask']
        assert config.site_name == 'Imported Site'
        assert config.mail_port == 2525
        assert config.blog_enabled is False


def test_import_config_rolls_back_on_invalid_owner_payload(modular_client, modular_app):
    login_admin(modular_client)

    # owner_profile should be a dict; passing string forces AttributeError (.get)
    response = modular_client.post('/admin/import-config', json={
        'owner_profile': 'invalid-shape'
    })
    assert response.status_code == 400
    assert response.get_json()['success'] is False

    with modular_app.app_context():
        assert OwnerProfile.query.first() is None


def test_contact_info_and_about_info_redirect_to_owner_profile(modular_client):
    login_admin(modular_client)

    contact_response = modular_client.get('/admin/contact-info', follow_redirects=False)
    about_response = modular_client.get('/admin/about-info', follow_redirects=False)

    assert contact_response.status_code == 302
    assert about_response.status_code == 302
    assert '/admin/owner-profile' in contact_response.headers.get('Location', '')
    assert '/admin/owner-profile' in about_response.headers.get('Location', '')


def test_contact_info_requires_authentication(modular_client):
    response = modular_client.get('/admin/contact-info', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/login' in response.headers.get('Location', '')
