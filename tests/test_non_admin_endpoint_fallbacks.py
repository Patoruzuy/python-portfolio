"""
Unit tests for non-admin endpoint alias fallback behavior.
"""

from flask import Flask, render_template_string
import pytest
from werkzeug.routing import BuildError

from app.utils.endpoint_url_fallbacks import install_endpoint_url_for_fallback


def _install_with_route(endpoint: str, rule: str = '/') -> Flask:
    app = Flask(__name__)
    app.add_url_rule(rule, endpoint, lambda: 'ok')
    install_endpoint_url_for_fallback(app)
    return app


def test_fallback_resolves_index_to_public_index():
    app = _install_with_route('public.index', '/')
    with app.test_request_context('/'):
        rendered = render_template_string("{{ url_for('index') }}")
        assert rendered == '/'


def test_fallback_resolves_public_blog_to_blog():
    app = _install_with_route('blog', '/blog')
    with app.test_request_context('/'):
        rendered = render_template_string("{{ url_for('public.blog') }}")
        assert rendered == '/blog'


def test_fallback_resolves_api_projects_alias():
    app = _install_with_route('api.api_projects', '/api/projects')
    with app.test_request_context('/'):
        rendered = render_template_string("{{ url_for('api_projects') }}")
        assert rendered == '/api/projects'


def test_fallback_resolves_privacy_policy_alias():
    app = _install_with_route('gdpr.privacy_policy', '/privacy-policy')
    with app.test_request_context('/'):
        rendered = render_template_string("{{ url_for('privacy_policy') }}")
        assert rendered == '/privacy-policy'


def test_fallback_still_raises_for_unknown_endpoint():
    app = _install_with_route('public.index', '/')
    with app.test_request_context('/'):
        with pytest.raises(BuildError):
            render_template_string("{{ url_for('totally_missing_endpoint') }}")
