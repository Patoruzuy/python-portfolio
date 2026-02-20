"""
In-process tests for GDPR endpoints using Flask test client.
"""

import json

from models import AnalyticsEvent, CookieConsent, PageView, SiteConfig, db


def _set_analytics_enabled(app) -> None:
    """Ensure analytics middleware is active for tracking-related tests."""
    with app.app_context():
        config = SiteConfig.query.first()
        if config is None:
            config = SiteConfig(site_name='Test Portfolio')
            db.session.add(config)
        config.analytics_enabled = True
        db.session.commit()


def test_cookie_consent_endpoint_records_decision(client, database, app):
    session_id = 'gdpr-consent-session'
    response = client.post(
        '/api/cookie-consent',
        json={
            'session_id': session_id,
            'consent_type': 'accepted',
            'categories': ['necessary', 'analytics']
        }
    )

    assert response.status_code == 201
    assert response.get_json()['success'] is True

    with app.app_context():
        consent = CookieConsent.query.filter_by(session_id=session_id).first()
        assert consent is not None
        assert consent.consent_type == 'accepted'
        assert consent.categories_accepted == ['necessary', 'analytics']


def test_my_data_page_loads(client, database):
    response = client.get('/my-data')
    assert response.status_code == 200


def test_data_download_requires_session_cookie(client, database):
    response = client.get('/api/my-data/download')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'No session found'


def test_data_download_exports_session_data(client, database, app):
    session_id = 'gdpr-export-session'

    with app.app_context():
        db.session.add(PageView(path='/about', session_id=session_id))
        db.session.add(
            AnalyticsEvent(
                session_id=session_id,
                event_type='click',
                event_name='cta-click',
                page_path='/about',
                element_id='contact-button',
                event_data={'source': 'hero'}
            )
        )
        db.session.add(
            CookieConsent(
                session_id=session_id,
                consent_type='partial',
                categories_accepted=['necessary']
            )
        )
        db.session.commit()

    client.set_cookie('analytics_session', session_id)
    response = client.get('/api/my-data/download')

    assert response.status_code == 200
    assert response.content_type.startswith('application/json')

    payload = json.loads(response.data)
    assert payload['session_id'] == session_id
    assert len(payload['page_views']) == 1
    assert len(payload['events']) == 1
    assert len(payload['consent_history']) == 1


def test_dnt_header_prevents_page_tracking(client, database, app):
    session_id = 'gdpr-dnt-session'
    _set_analytics_enabled(app)

    client.set_cookie('analytics_session', session_id)
    client.set_cookie('cookie_consent', 'accepted')

    response = client.get('/', headers={'DNT': '1'})
    assert response.status_code == 200

    with app.app_context():
        tracked_view = PageView.query.filter_by(session_id=session_id, path='/').first()
        assert tracked_view is None


def test_granular_consent_categories_are_persisted(client, database, app):
    session_id = 'gdpr-granular-session'
    categories = ['necessary', 'analytics']

    response = client.post(
        '/api/cookie-consent',
        json={
            'session_id': session_id,
            'consent_type': 'partial',
            'categories': categories
        }
    )

    assert response.status_code == 201

    with app.app_context():
        consent = CookieConsent.query.filter_by(session_id=session_id).first()
        assert consent is not None
        assert consent.consent_type == 'partial'
        assert consent.categories_accepted == categories
