"""
Template URL endpoint fallback helpers for route modularization.

This allows templates to render in both layouts:
- Monolithic route names (e.g. ``index`` or ``admin.dashboard``)
- Modular blueprint route names (e.g. ``public.index`` or ``admin_dashboard.dashboard``)
"""

from __future__ import annotations

from typing import Dict, List, Sequence

from flask import Flask, current_app, url_for as flask_url_for
from werkzeug.routing import BuildError

# Explicit endpoint aliases between modular and monolithic route names.
_ENDPOINT_PAIRS: Sequence[tuple[str, str]] = (
    # Public routes
    ('public.index', 'index'),
    ('public.projects', 'projects'),
    ('public.project_detail', 'project_detail'),
    ('public.raspberry_pi', 'raspberry_pi'),
    ('public.rpi_resources', 'rpi_resources'),
    ('public.blog', 'blog'),
    ('public.blog_post', 'blog_post'),
    ('public.products', 'products'),
    ('public.about', 'about'),
    ('public.contact', 'contact'),
    # API routes
    ('api.api_projects', 'api_projects'),
    ('api.api_blog', 'api_blog'),
    ('api.api_contact', 'api_contact'),
    ('api.api_newsletter_subscribe', 'api_newsletter_subscribe'),
    ('api.newsletter_confirm', 'newsletter_confirm'),
    ('api.newsletter_unsubscribe', 'newsletter_unsubscribe'),
    # Analytics routes
    ('analytics.analytics_dashboard', 'analytics_dashboard'),
    ('analytics.track_analytics_event', 'track_analytics_event'),
    # GDPR routes
    ('gdpr.privacy_policy', 'privacy_policy'),
    ('gdpr.my_data_page', 'my_data_page'),
    ('gdpr.log_cookie_consent', 'log_cookie_consent'),
    ('gdpr.download_my_data', 'download_my_data'),
    ('gdpr.delete_my_data', 'delete_my_data'),
    # Admin routes
    ('admin_auth.login', 'admin.login'),
    ('admin_auth.logout', 'admin.logout'),
    ('admin_auth.forgot_password', 'admin.forgot_password'),
    ('admin_auth.security_settings', 'admin.security_settings'),
    ('admin_dashboard.dashboard', 'admin.dashboard'),
    ('admin_dashboard.analytics', 'admin.analytics'),
    ('admin_newsletter.newsletter', 'admin.newsletter'),
    ('admin_newsletter.delete_subscriber', 'admin.delete_subscriber'),
    ('admin_projects.projects', 'admin.projects'),
    ('admin_projects.add_project', 'admin.add_project'),
    ('admin_projects.edit_project', 'admin.edit_project'),
    ('admin_projects.delete_project', 'admin.delete_project'),
    ('admin_projects.raspberry_pi', 'admin.raspberry_pi'),
    ('admin_projects.add_rpi_project', 'admin.add_rpi_project'),
    ('admin_projects.edit_rpi_project', 'admin.edit_rpi_project'),
    ('admin_projects.delete_rpi_project', 'admin.delete_rpi_project'),
    ('admin_products.products', 'admin.products'),
    ('admin_products.add_product', 'admin.add_product'),
    ('admin_products.edit_product', 'admin.edit_product'),
    ('admin_products.delete_product', 'admin.delete_product'),
    ('admin_blog.blog', 'admin.blog'),
    ('admin_blog.create_blog_post', 'admin.create_blog_post'),
    ('admin_blog.edit_blog_post', 'admin.edit_blog_post'),
    ('admin_blog.delete_blog_post', 'admin.delete_blog_post'),
    ('admin_settings.owner_profile', 'admin.owner_profile'),
    ('admin_settings.site_config', 'admin.site_config'),
    ('admin_settings.export_config', 'admin.export_config'),
    ('admin_settings.import_config', 'admin.import_config'),
    ('admin_settings.contact_info', 'admin.contact_info'),
    ('admin_settings.about_info', 'admin.about_info'),
    ('admin_media.upload_image', 'admin.upload_image'),
)


def _build_alias_map() -> Dict[str, List[str]]:
    aliases: Dict[str, List[str]] = {}
    for first, second in _ENDPOINT_PAIRS:
        aliases.setdefault(first, []).append(second)
        aliases.setdefault(second, []).append(first)
    return aliases


ENDPOINT_ALIASES: Dict[str, List[str]] = _build_alias_map()


def resolve_endpoint_alias(endpoint: str) -> str:
    """Return the first aliased endpoint name that exists in the current app."""
    if endpoint in current_app.view_functions:
        return endpoint

    for candidate in ENDPOINT_ALIASES.get(endpoint, []):
        if candidate in current_app.view_functions:
            return candidate

    return endpoint


def resolve_admin_endpoint(endpoint: str) -> str:
    """Backward-compatible wrapper for existing callers."""
    return resolve_endpoint_alias(endpoint)


def install_endpoint_url_for_fallback(app: Flask) -> None:
    """Install a template-only ``url_for`` fallback for endpoint aliases."""

    def url_for_with_endpoint_fallback(endpoint: str, **values: object) -> str:
        if not isinstance(endpoint, str):
            return flask_url_for(endpoint, **values)

        resolved = resolve_endpoint_alias(endpoint)
        try:
            return flask_url_for(resolved, **values)
        except BuildError as original_error:
            for candidate in ENDPOINT_ALIASES.get(endpoint, []):
                try:
                    return flask_url_for(candidate, **values)
                except BuildError:
                    continue
            raise original_error

    app.jinja_env.globals['url_for'] = url_for_with_endpoint_fallback


def install_admin_url_for_fallback(app: Flask) -> None:
    """Backward-compatible alias for older imports."""
    install_endpoint_url_for_fallback(app)

