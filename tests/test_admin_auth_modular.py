"""
Coverage-focused tests for modular admin auth routes.

These tests target routes/admin/auth.py through app_factory.create_app().
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from werkzeug.security import generate_password_hash

from app_factory import create_app
from models import db
from routes.admin import auth as auth_routes


@pytest.fixture
def modular_app():
    app = create_app('testing')
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
        ADMIN_USERNAME='admin',
        ADMIN_PASSWORD_HASH=generate_password_hash('correct-password'),
        REMEMBER_COOKIE_DURATION=timedelta(days=7),
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


def login_session(client, remember: bool | None = None) -> None:
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        if remember is True:
            sess['remember_me'] = True


def test_login_get_renders(modular_client):
    response = modular_client.get('/admin/login')
    assert response.status_code == 200


def test_login_redirects_when_already_logged_in(modular_client):
    login_session(modular_client)

    response = modular_client.get('/admin/login', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/dashboard' in response.headers.get('Location', '')


def test_login_success_without_remember_me(modular_client):
    response = modular_client.post(
        '/admin/login',
        data={'username': 'admin', 'password': 'correct-password'},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with modular_client.session_transaction() as sess:
        assert sess.get('admin_logged_in') is True
        assert 'remember_me' not in sess


def test_login_success_with_remember_me(modular_client):
    response = modular_client.post(
        '/admin/login',
        data={'username': 'admin', 'password': 'correct-password', 'remember': 'on'},
        follow_redirects=False,
    )

    assert response.status_code == 302
    with modular_client.session_transaction() as sess:
        assert sess.get('admin_logged_in') is True
        assert sess.get('remember_me') is True


def test_login_fails_with_invalid_credentials(modular_client):
    response = modular_client.post(
        '/admin/login',
        data={'username': 'admin', 'password': 'wrong-password'},
    )
    assert response.status_code == 200


def test_login_handles_missing_password_hash_configuration(modular_client, monkeypatch):
    monkeypatch.setattr(auth_routes, 'get_admin_password_hash', lambda: None)

    response = modular_client.post(
        '/admin/login',
        data={'username': 'admin', 'password': 'anything'},
    )

    assert response.status_code == 200


def test_logout_clears_session_and_redirects(modular_client):
    login_session(modular_client, remember=True)

    response = modular_client.get('/admin/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/login' in response.headers.get('Location', '')

    with modular_client.session_transaction() as sess:
        assert 'admin_logged_in' not in sess
        assert 'remember_me' not in sess


def test_forgot_password_get_and_missing_new_password_branch(modular_client):
    get_response = modular_client.get('/admin/forgot-password')
    assert get_response.status_code == 200

    post_response = modular_client.post(
        '/admin/forgot-password',
        data={'recovery_code': 'ABC123'},
    )
    assert post_response.status_code == 200


def test_forgot_password_valid_recovery_code_path(modular_client, monkeypatch):
    calls = {'remaining': 0}

    def fake_verify_and_use(code):
        return code == 'VALID-CODE'

    def fake_remaining_count():
        calls['remaining'] += 1
        return 3 if calls['remaining'] == 1 else 2

    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'verify_and_use', staticmethod(fake_verify_and_use))
    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'get_remaining_count', staticmethod(fake_remaining_count))

    response = modular_client.post(
        '/admin/forgot-password',
        data={'recovery_code': 'VALID-CODE', 'new_password': 'new-pass-123'},
    )

    assert response.status_code == 200


def test_forgot_password_invalid_recovery_code_path(modular_client, monkeypatch):
    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'verify_and_use', staticmethod(lambda _code: False))
    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'get_remaining_count', staticmethod(lambda: 5))

    response = modular_client.post(
        '/admin/forgot-password',
        data={'recovery_code': 'INVALID', 'new_password': 'new-pass-123'},
    )

    assert response.status_code == 200


def test_forgot_password_legacy_fallback_paths(modular_client, monkeypatch):
    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'get_remaining_count', staticmethod(lambda: 0))
    no_codes_response = modular_client.post(
        '/admin/forgot-password',
        data={'new_password': 'legacy-pass-1'},
    )
    assert no_codes_response.status_code == 200

    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'get_remaining_count', staticmethod(lambda: 4))
    with_codes_response = modular_client.post(
        '/admin/forgot-password',
        data={'new_password': 'legacy-pass-2'},
    )
    assert with_codes_response.status_code == 200


def test_security_settings_requires_authentication(modular_client):
    response = modular_client.get('/admin/security', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/login' in response.headers.get('Location', '')


def test_security_settings_get_and_generate_codes(modular_client, monkeypatch):
    login_session(modular_client)

    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'get_remaining_count', staticmethod(lambda: 1))
    get_response = modular_client.get('/admin/security')
    assert get_response.status_code == 200

    monkeypatch.setattr(auth_routes.AdminRecoveryCode, 'generate_codes', staticmethod(lambda _count: ['A', 'B']))
    post_response = modular_client.post('/admin/security', data={'action': 'generate_codes'})
    assert post_response.status_code == 200
