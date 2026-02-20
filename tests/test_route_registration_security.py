"""
Regression tests for modular route registration security behavior.
"""

from flask import Flask, url_for

from routes import register_all_blueprints
from routes.admin import register_admin_blueprints


class DummyCSRF:
    """Collects exempted view functions for assertions."""

    def __init__(self) -> None:
        self.exempted = []

    def exempt(self, view_func):
        self.exempted.append(view_func)
        return view_func


def _create_registered_app(include_admin: bool = False) -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.extensions['csrf'] = DummyCSRF()
    register_all_blueprints(app)
    if include_admin:
        register_admin_blueprints(app)
    return app


def test_register_all_blueprints_exempts_expected_api_post_endpoints_from_csrf():
    app = _create_registered_app()
    exempted_names = {view.__name__ for view in app.extensions['csrf'].exempted}
    assert 'api_contact' in exempted_names
    assert 'api_newsletter_subscribe' in exempted_names


def test_register_all_blueprints_exposes_newsletter_links_without_api_prefix():
    app = _create_registered_app()
    with app.test_request_context('/'):
        confirm_url = url_for('newsletter_confirm', token='abc123')
        unsubscribe_url = url_for('newsletter_unsubscribe', token='abc123')

    assert confirm_url == '/newsletter/confirm/abc123'
    assert unsubscribe_url == '/newsletter/unsubscribe/abc123'


def test_modular_admin_analytics_requires_authentication():
    app = _create_registered_app(include_admin=True)
    client = app.test_client()
    response = client.get('/admin/analytics')

    assert response.status_code == 302
    assert '/admin/login' in response.headers.get('Location', '')

