"""
Coverage-focused tests for modular GDPR routes.

These tests target routes/gdpr.py through app_factory.create_app().
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.app_factory import create_app
from app.models import AnalyticsEvent, CookieConsent, PageView, UserSession, db
from app.routes import gdpr as gdpr_routes


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


def test_privacy_policy_and_my_data_pages_render(modular_client):
    privacy = modular_client.get('/privacy-policy')
    my_data = modular_client.get('/my-data')

    assert privacy.status_code == 200
    assert my_data.status_code == 200


def test_cookie_consent_logs_successfully(modular_client, modular_app):
    modular_client.set_cookie('analytics_session', 'consent-session-1')

    response = modular_client.post(
        '/api/cookie-consent',
        json={
            'consent_type': 'accepted',
            'categories': ['necessary', 'analytics'],
        },
        headers={'User-Agent': 'GDPRTest/1.0'},
    )

    assert response.status_code == 201
    assert response.get_json()['success'] is True

    with modular_app.app_context():
        consent = CookieConsent.query.filter_by(session_id='consent-session-1').first()
        assert consent is not None
        assert consent.consent_type == 'accepted'
        assert consent.categories_accepted == ['necessary', 'analytics']
        assert consent.user_agent == 'GDPRTest/1.0'


def test_cookie_consent_returns_400_for_null_json(modular_client):
    response = modular_client.post('/api/cookie-consent', data='null', content_type='application/json')
    assert response.status_code == 400
    assert response.get_json()['success'] is False


def test_cookie_consent_returns_500_on_db_error(modular_client, monkeypatch):
    def fail_add(_obj):
        raise RuntimeError('db add failed')

    monkeypatch.setattr(db.session, 'add', fail_add)

    response = modular_client.post(
        '/api/cookie-consent',
        json={'session_id': 'boom-session', 'consent_type': 'accepted'},
    )

    assert response.status_code == 500
    assert response.get_json()['success'] is False


def test_download_my_data_returns_404_without_session(modular_client):
    response = modular_client.get('/api/my-data/download')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'No session found'


def test_download_my_data_exports_pageviews_events_and_consents(modular_client, modular_app):
    session_id = 'download-session-1'
    modular_client.set_cookie('analytics_session', session_id)

    with modular_app.app_context():
        db.session.add(
            PageView(
                session_id=session_id,
                path='/projects',
                created_at=datetime.now(timezone.utc),
                referrer='https://example.com',
                device_type='desktop',
                browser='Chrome',
                os='Windows',
            )
        )
        db.session.add(
            AnalyticsEvent(
                session_id=session_id,
                event_type='click',
                event_name='download-button',
                page_path='/projects',
                created_at=datetime.now(timezone.utc),
            )
        )
        db.session.add(
            CookieConsent(
                session_id=session_id,
                consent_type='accepted',
                categories_accepted=['necessary', 'analytics'],
                created_at=datetime.now(timezone.utc),
            )
        )
        db.session.commit()

    response = modular_client.get('/api/my-data/download')
    assert response.status_code == 200
    assert response.mimetype == 'application/json'

    payload = json.loads(response.data)
    assert payload['session_id'] == session_id
    assert len(payload['page_views']) == 1
    assert payload['page_views'][0]['path'] == '/projects'
    assert len(payload['events']) == 1
    assert payload['events'][0]['event_name'] == 'download-button'
    assert len(payload['consent_history']) == 1
    assert payload['consent_history'][0]['consent_type'] == 'accepted'


def test_download_my_data_returns_500_on_send_file_failure(modular_client, monkeypatch):
    modular_client.set_cookie('analytics_session', 'download-session-error')

    monkeypatch.setattr(
        gdpr_routes,
        'send_file',
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError('send failure')),
    )

    response = modular_client.get('/api/my-data/download')
    assert response.status_code == 500
    assert response.get_json()['error'] == 'Export failed'


def test_delete_my_data_returns_404_without_session(modular_client):
    response = modular_client.post('/api/my-data/delete')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'No session found'


def test_delete_my_data_removes_analytics_data_but_keeps_consent(modular_client, modular_app):
    session_id = 'delete-session-1'
    modular_client.set_cookie('analytics_session', session_id)

    with modular_app.app_context():
        db.session.add(PageView(session_id=session_id, path='/blog'))
        db.session.add(AnalyticsEvent(session_id=session_id, event_type='click', event_name='x'))
        db.session.add(UserSession(session_id=session_id))
        db.session.add(CookieConsent(session_id=session_id, consent_type='accepted', categories_accepted=['necessary']))
        db.session.commit()

    response = modular_client.post('/api/my-data/delete')
    assert response.status_code == 200
    assert response.get_json()['success'] is True

    with modular_app.app_context():
        assert PageView.query.filter_by(session_id=session_id).count() == 0
        assert AnalyticsEvent.query.filter_by(session_id=session_id).count() == 0
        assert UserSession.query.filter_by(session_id=session_id).count() == 0
        assert CookieConsent.query.filter_by(session_id=session_id).count() == 1


def test_delete_my_data_returns_500_on_commit_error(modular_client, modular_app, monkeypatch):
    session_id = 'delete-session-error'
    modular_client.set_cookie('analytics_session', session_id)

    with modular_app.app_context():
        db.session.add(PageView(session_id=session_id, path='/about'))
        db.session.commit()

    monkeypatch.setattr(db.session, 'commit', lambda: (_ for _ in ()).throw(RuntimeError('commit failed')))

    response = modular_client.post('/api/my-data/delete')
    assert response.status_code == 500
    assert response.get_json()['error'] == 'Deletion failed'
