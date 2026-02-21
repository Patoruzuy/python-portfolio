"""
Utility modules for the Python Portfolio application.

This package contains helper functions and utilities used throughout the application.
"""

from .csp_manager import init_csp, get_csp_manager
from .analytics_utils import (
    parse_user_agent,
    get_or_create_session,
    get_analytics_summary,
    get_daily_traffic,
    track_event
)
from .video_utils import validate_video_url

__all__ = [
    'init_csp',
    'get_csp_manager',
    'parse_user_agent',
    'get_or_create_session',
    'get_analytics_summary',
    'get_daily_traffic',
    'track_event',
    'validate_video_url'
]
