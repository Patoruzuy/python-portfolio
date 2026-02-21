"""Backward-compatible wrapper for renamed endpoint fallback utilities."""

from app.utils.endpoint_url_fallbacks import (
    ENDPOINT_ALIASES,
    install_admin_url_for_fallback,
    install_endpoint_url_for_fallback,
    resolve_admin_endpoint,
    resolve_endpoint_alias,
)

__all__ = [
    'ENDPOINT_ALIASES',
    'install_admin_url_for_fallback',
    'install_endpoint_url_for_fallback',
    'resolve_admin_endpoint',
    'resolve_endpoint_alias',
]
