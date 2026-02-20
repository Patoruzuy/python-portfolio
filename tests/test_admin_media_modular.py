"""
Coverage-focused tests for modular admin media routes.

These tests target routes/admin/media.py through app_factory.create_app().
"""

from __future__ import annotations

from io import BytesIO

import pytest

from app_factory import create_app
from models import db
from routes.admin import media as media_routes


@pytest.fixture
def modular_app(tmp_path):
    app = create_app('testing')
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
        UPLOAD_FOLDER=str(tmp_path / 'uploads'),
        UPLOAD_URL_PREFIX='/uploads',
        ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
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
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True


def test_upload_image_requires_authentication(modular_client):
    response = modular_client.get('/admin/upload-image', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/login' in response.headers.get('Location', '')


def test_upload_image_popup_get_uses_popup_template(modular_client):
    login_admin(modular_client)

    response = modular_client.get('/admin/upload-image?popup=true')
    assert response.status_code == 200
    assert b'name="popup" value="true"' in response.data


def test_upload_image_post_missing_file_returns_400(modular_client):
    login_admin(modular_client)

    response = modular_client.post('/admin/upload-image', data={})
    assert response.status_code == 400
    assert b'Upload Image' in response.data


def test_upload_image_post_empty_filename_returns_400(modular_client):
    login_admin(modular_client)

    response = modular_client.post(
        '/admin/upload-image',
        data={'image': (BytesIO(b'abc'), '')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 400
    assert b'Upload Image' in response.data


def test_upload_image_post_validation_failure_returns_400(modular_client, monkeypatch):
    login_admin(modular_client)

    monkeypatch.setattr(
        media_routes,
        'validate_uploaded_image',
        lambda _file, _exts: (False, 'Invalid image payload'),
    )

    response = modular_client.post(
        '/admin/upload-image',
        data={'image': (BytesIO(b'not-image'), 'bad.png')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 400
    assert b'Upload Image' in response.data


def test_upload_image_post_invalid_secure_filename_returns_400(modular_client, monkeypatch):
    login_admin(modular_client)

    monkeypatch.setattr(
        media_routes,
        'validate_uploaded_image',
        lambda _file, _exts: (True, ''),
    )

    response = modular_client.post(
        '/admin/upload-image',
        data={'image': (BytesIO(b'payload'), '..')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 400
    assert b'Upload Image' in response.data


def test_upload_image_post_path_resolution_error_returns_400(modular_client, monkeypatch):
    login_admin(modular_client)

    monkeypatch.setattr(
        media_routes,
        'validate_uploaded_image',
        lambda _file, _exts: (True, ''),
    )
    monkeypatch.setattr(
        media_routes,
        'resolve_upload_filepath',
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError('Invalid upload destination path.')),
    )

    response = modular_client.post(
        '/admin/upload-image',
        data={'image': (BytesIO(b'payload'), 'safe.png')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 400
    assert b'Upload Image' in response.data


def test_upload_image_post_success_saves_file_and_renders_uploaded_path(modular_client, modular_app, monkeypatch, tmp_path):
    login_admin(modular_client)

    monkeypatch.setattr(
        media_routes,
        'validate_uploaded_image',
        lambda _file, _exts: (True, ''),
    )

    response = modular_client.post(
        '/admin/upload-image',
        data={'image': (BytesIO(b'valid-image-bytes'), 'hero.png')},
        content_type='multipart/form-data',
    )

    assert response.status_code == 200
    assert b'/uploads/hero_' in response.data
    assert b'.png' in response.data

    upload_dir = tmp_path / 'uploads'
    saved = list(upload_dir.iterdir())
    assert len(saved) == 1
    assert saved[0].name.startswith('hero_')
    assert saved[0].suffix == '.png'
