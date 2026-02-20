"""
Coverage-focused tests for modular API routes.

These tests target routes/api.py through app_factory.create_app().
"""

from __future__ import annotations

import sys
import types
from datetime import datetime, timezone

import pytest
from flask import Flask

from app_factory import create_app
from models import BlogPost, Newsletter, Project, db
from routes import api as api_routes

ORIGINAL_GET_LIMITER = api_routes.get_limiter


class _AsyncTaskStub:
    """Small stub object that mimics Celery task wrappers with .delay()."""

    def __init__(self, result=None, exc: Exception | None = None):
        self._result = result
        self._exc = exc

    def delay(self, *args, **kwargs):
        if self._exc is not None:
            raise self._exc
        if self._result is not None:
            return self._result
        return types.SimpleNamespace(id='task-default')


class _LimiterStub:
    def __init__(self):
        self.applied_limits = []

    def limit(self, spec):
        self.applied_limits.append(spec)

        def decorator(func):
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapped

        return decorator


def _install_email_task_stubs(
    monkeypatch,
    *,
    contact_result=None,
    contact_exc: Exception | None = None,
    newsletter_result=None,
    newsletter_exc: Exception | None = None,
):
    fake_module = types.SimpleNamespace(
        send_contact_email=_AsyncTaskStub(result=contact_result, exc=contact_exc),
        send_newsletter_confirmation=_AsyncTaskStub(result=newsletter_result, exc=newsletter_exc),
    )
    monkeypatch.setitem(sys.modules, 'tasks.email_tasks', fake_module)


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


@pytest.fixture(autouse=True)
def _disable_rate_limiter_by_default(monkeypatch):
    # Keep tests deterministic; enable limiter explicitly per test when needed.
    monkeypatch.setattr(api_routes, 'get_limiter', lambda: None)


def test_get_limiter_returns_extension_value():
    app = Flask(__name__)
    marker = object()
    app.extensions['limiter'] = marker

    with app.app_context():
        assert ORIGINAL_GET_LIMITER() is marker


def test_register_api_csrf_exemptions_is_noop_without_csrf():
    app = Flask(__name__)
    api_routes.register_api_csrf_exemptions(app)


def test_api_projects_filters_by_category_and_technology(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add_all(
            [
                Project(
                    title='Web A',
                    description='Desc',
                    technologies='Python,Flask',
                    category='web',
                ),
                Project(
                    title='Web B',
                    description='Desc',
                    technologies='JavaScript,React',
                    category='web',
                ),
                Project(
                    title='Data C',
                    description='Desc',
                    technologies='Python,Airflow',
                    category='data',
                ),
            ]
        )
        db.session.commit()

    response = modular_client.get('/api/projects?category=web&technology=Python')
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]['title'] == 'Web A'
    assert payload[0]['technologies'] == ['Python', 'Flask']


def test_api_blog_filters_published_posts(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add_all(
            [
                BlogPost(
                    title='Intro Flask',
                    slug='intro-flask',
                    excerpt='Flask intro',
                    author='Tester',
                    content='Body',
                    category='Tutorial',
                    tags='python,flask',
                    published=True,
                    view_count=10,
                ),
                BlogPost(
                    title='Draft Flask',
                    slug='draft-flask',
                    excerpt='Draft',
                    author='Tester',
                    content='Body',
                    category='Tutorial',
                    tags='python,flask',
                    published=False,
                ),
            ]
        )
        db.session.commit()

    response = modular_client.get('/api/blog?category=Tutorial&tag=flask')
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]['title'] == 'Intro Flask'


def test_api_contact_returns_400_for_missing_required_field(modular_client):
    response = modular_client.post('/api/contact', json={'name': 'Only Name'})
    assert response.status_code == 400
    body = response.get_json()
    assert body['success'] is False
    assert 'Missing required field' in body['error']


def test_api_contact_success_with_limiter_and_form_payload(modular_client, monkeypatch):
    limiter = _LimiterStub()
    monkeypatch.setattr(api_routes, 'get_limiter', lambda: limiter)
    _install_email_task_stubs(
        monkeypatch,
        contact_result=types.SimpleNamespace(id='contact-task-123'),
    )

    response = modular_client.post(
        '/api/contact',
        data={
            'name': 'Alex',
            'email': 'alex@example.com',
            'subject': 'Hi',
            'message': 'Testing contact route',
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body['success'] is True
    assert body['task_id'] == 'contact-task-123'
    assert limiter.applied_limits == [api_routes.RATE_LIMITS['api_contact']]


def test_api_contact_returns_500_when_queueing_fails(modular_client, monkeypatch):
    _install_email_task_stubs(monkeypatch, contact_exc=RuntimeError('queue unavailable'))

    response = modular_client.post(
        '/api/contact',
        json={
            'name': 'Alex',
            'email': 'alex@example.com',
            'subject': 'Hi',
            'message': 'Testing error path',
        },
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body['success'] is False


def test_newsletter_subscribe_rejects_invalid_email(modular_client):
    response = modular_client.post('/api/newsletter/subscribe', json={'email': 'invalid-email'})
    assert response.status_code == 400
    body = response.get_json()
    assert body['success'] is False


def test_newsletter_subscribe_rejects_active_duplicate(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(Newsletter(email='dup@example.com', active=True, confirmed=True))
        db.session.commit()

    response = modular_client.post('/api/newsletter/subscribe', json={'email': 'dup@example.com'})
    assert response.status_code == 400
    body = response.get_json()
    assert body['success'] is False
    assert 'already subscribed' in body['error']


def test_newsletter_subscribe_reactivates_inactive_subscription(modular_client, modular_app):
    with modular_app.app_context():
        sub = Newsletter(
            email='inactive@example.com',
            active=False,
            confirmed=False,
            unsubscribed_at=datetime.now(timezone.utc),
        )
        db.session.add(sub)
        db.session.commit()

    response = modular_client.post('/api/newsletter/subscribe', json={'email': 'inactive@example.com'})
    assert response.status_code == 200
    body = response.get_json()
    assert body['success'] is True

    with modular_app.app_context():
        sub = Newsletter.query.filter_by(email='inactive@example.com').first()
        assert sub is not None
        assert sub.active is True
        assert sub.unsubscribed_at is None


def test_newsletter_subscribe_success_when_confirmation_queue_fails(modular_client, modular_app, monkeypatch):
    limiter = _LimiterStub()
    monkeypatch.setattr(api_routes, 'get_limiter', lambda: limiter)
    _install_email_task_stubs(monkeypatch, newsletter_exc=RuntimeError('broker down'))

    response = modular_client.post(
        '/api/newsletter/subscribe',
        json={'email': 'newsub@example.com', 'name': 'New Sub'},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body['success'] is True
    assert limiter.applied_limits == [api_routes.RATE_LIMITS['api_newsletter']]

    with modular_app.app_context():
        sub = Newsletter.query.filter_by(email='newsub@example.com').first()
        assert sub is not None
        assert sub.confirmation_token


def test_newsletter_subscribe_returns_500_when_commit_fails(modular_client, modular_app, monkeypatch):
    _install_email_task_stubs(monkeypatch)

    with modular_app.app_context():
        original_commit = db.session.commit

    def fail_commit():
        raise RuntimeError('db commit failure')

    monkeypatch.setattr(db.session, 'commit', fail_commit)
    response = modular_client.post('/api/newsletter/subscribe', json={'email': 'boom@example.com'})
    assert response.status_code == 500
    body = response.get_json()
    assert body['success'] is False

    # Restore for safe assertion query path.
    monkeypatch.setattr(db.session, 'commit', original_commit)
    with modular_app.app_context():
        assert Newsletter.query.filter_by(email='boom@example.com').first() is None


def test_newsletter_confirm_invalid_token_redirects(modular_client):
    response = modular_client.get('/newsletter/confirm/invalid-token')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/blog')


def test_newsletter_confirm_already_confirmed_redirects(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(
            Newsletter(
                email='confirmed@example.com',
                confirmation_token='confirmed-token',
                confirmed=True,
            )
        )
        db.session.commit()

    response = modular_client.get('/newsletter/confirm/confirmed-token')
    assert response.status_code == 302


def test_newsletter_confirm_sets_confirmed_true(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(
            Newsletter(
                email='pending@example.com',
                confirmation_token='pending-token',
                confirmed=False,
            )
        )
        db.session.commit()

    response = modular_client.get('/newsletter/confirm/pending-token')
    assert response.status_code == 302

    with modular_app.app_context():
        sub = Newsletter.query.filter_by(confirmation_token='pending-token').first()
        assert sub is not None
        assert sub.confirmed is True


def test_newsletter_confirm_handles_commit_exception(modular_client, modular_app, monkeypatch):
    with modular_app.app_context():
        db.session.add(
            Newsletter(
                email='error-confirm@example.com',
                confirmation_token='confirm-error-token',
                confirmed=False,
            )
        )
        db.session.commit()
        original_commit = db.session.commit

    monkeypatch.setattr(db.session, 'commit', lambda: (_ for _ in ()).throw(RuntimeError('commit failed')))

    response = modular_client.get('/newsletter/confirm/confirm-error-token')
    assert response.status_code == 302

    monkeypatch.setattr(db.session, 'commit', original_commit)


def test_newsletter_unsubscribe_invalid_token_redirects(modular_client):
    response = modular_client.get('/newsletter/unsubscribe/invalid-token')
    assert response.status_code == 302


def test_newsletter_unsubscribe_already_inactive_redirects(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(
            Newsletter(
                email='inactive@example.com',
                confirmation_token='inactive-token',
                active=False,
            )
        )
        db.session.commit()

    response = modular_client.get('/newsletter/unsubscribe/inactive-token')
    assert response.status_code == 302


def test_newsletter_unsubscribe_sets_inactive_and_timestamp(modular_client, modular_app):
    with modular_app.app_context():
        db.session.add(
            Newsletter(
                email='active@example.com',
                confirmation_token='active-token',
                active=True,
            )
        )
        db.session.commit()

    response = modular_client.get('/newsletter/unsubscribe/active-token')
    assert response.status_code == 302

    with modular_app.app_context():
        sub = Newsletter.query.filter_by(confirmation_token='active-token').first()
        assert sub is not None
        assert sub.active is False
        assert sub.unsubscribed_at is not None


def test_newsletter_unsubscribe_handles_commit_exception(modular_client, modular_app, monkeypatch):
    with modular_app.app_context():
        db.session.add(
            Newsletter(
                email='error-unsub@example.com',
                confirmation_token='unsub-error-token',
                active=True,
            )
        )
        db.session.commit()
        original_commit = db.session.commit

    monkeypatch.setattr(db.session, 'commit', lambda: (_ for _ in ()).throw(RuntimeError('commit failed')))

    response = modular_client.get('/newsletter/unsubscribe/unsub-error-token')
    assert response.status_code == 302

    monkeypatch.setattr(db.session, 'commit', original_commit)
