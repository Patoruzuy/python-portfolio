"""
Admin shared utilities and decorators.
Common functions used across all admin sub-blueprints.
"""
import os
from flask import current_app, session, redirect, url_for
from functools import wraps
from typing import Optional, Any, Callable, Set
from datetime import timedelta


def get_limiter() -> Optional[Any]:
    """Get limiter instance from app context."""
    return getattr(current_app, 'limiter', None)


def get_admin_username() -> str:
    """Get admin username from config."""
    return str(current_app.config.get('ADMIN_USERNAME', 'admin'))


def get_admin_password_hash() -> Optional[str]:
    """Get admin password hash from config."""
    return current_app.config.get('ADMIN_PASSWORD_HASH')


def get_upload_folder() -> str:
    """Get upload folder path from config."""
    return str(current_app.config.get('UPLOAD_FOLDER', 'static/images'))


def get_allowed_extensions() -> Set[str]:
    """Get allowed file extensions from config."""
    extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return set(extensions)


def get_upload_url_prefix(upload_folder: Optional[str] = None) -> str:
    """
    Resolve the public URL prefix for uploaded files.

    If UPLOAD_URL_PREFIX is not set, derive from UPLOAD_FOLDER when it is
    located under Flask's static folder.
    """
    configured_prefix = str(current_app.config.get('UPLOAD_URL_PREFIX', '')).strip()
    if configured_prefix:
        return f"/{configured_prefix.strip('/')}"

    resolved_upload_folder = os.path.abspath(upload_folder or get_upload_folder())
    static_folder = os.path.abspath(current_app.static_folder or 'static')

    try:
        common_path = os.path.commonpath([resolved_upload_folder, static_folder])
    except ValueError as exc:
        raise ValueError(
            'Invalid upload path configuration. Set UPLOAD_FOLDER to a valid path.'
        ) from exc

    if common_path != static_folder:
        raise ValueError(
            'UPLOAD_FOLDER is outside /static. Set UPLOAD_URL_PREFIX for custom upload serving.'
        )

    relative_path = os.path.relpath(resolved_upload_folder, static_folder)
    if relative_path in {'', '.'}:
        return '/static'

    return f"/static/{relative_path.replace(os.sep, '/').strip('/')}"


def build_uploaded_image_url(filename: str, upload_folder: Optional[str] = None) -> str:
    """Build the public URL for an uploaded filename."""
    prefix = get_upload_url_prefix(upload_folder).rstrip('/')
    if not prefix:
        return f"/{filename}"
    return f"{prefix}/{filename}"


def resolve_upload_filepath(upload_folder: str, filename: str) -> str:
    """Create and validate the absolute destination path for uploaded files."""
    absolute_upload_folder = os.path.abspath(upload_folder)
    os.makedirs(absolute_upload_folder, exist_ok=True)

    filepath = os.path.abspath(os.path.join(absolute_upload_folder, filename))
    if os.path.commonpath([absolute_upload_folder, filepath]) != absolute_upload_folder:
        raise ValueError('Invalid upload destination path.')

    return filepath


def get_dashboard_endpoint() -> str:
    """Resolve the available admin dashboard endpoint across app layouts."""
    view_functions = current_app.view_functions
    if 'admin_dashboard.dashboard' in view_functions:
        return 'admin_dashboard.dashboard'
    if 'admin.dashboard' in view_functions:
        return 'admin.dashboard'
    return 'admin_dashboard.dashboard'


def is_truthy(value: Any) -> bool:
    """Interpret common truthy form values."""
    return str(value).strip().lower() in {'1', 'true', 'on', 'yes'}


def parse_optional_int(value: Any) -> Optional[int]:
    """Safely parse optional integer values from forms."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def login_required(f: Callable) -> Callable:
    """Decorator to require admin login for routes."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename: str) -> bool:
    """Check if filename has allowed extension."""
    allowed_exts = get_allowed_extensions()
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts


def make_session_permanent() -> None:
    """Make session permanent with 30-minute default lifetime."""
    session.permanent = True
    if 'remember_me' not in session:
        current_app.permanent_session_lifetime = timedelta(minutes=30)
