"""
Admin authentication routes.
Handles login, logout, password reset, and security settings.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.wrappers.response import Response as WerkzeugResponse
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta
from typing import Union
from models import AdminRecoveryCode
from routes.admin.utils import (
    get_admin_username, get_admin_password_hash, 
    login_required, make_session_permanent
)

# Create admin auth blueprint
admin_auth_bp = Blueprint('admin_auth', __name__, url_prefix='/admin')


@admin_auth_bp.before_request
def before_request() -> None:
    """Make session permanent before each request."""
    make_session_permanent()


@admin_auth_bp.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, WerkzeugResponse]:
    """Admin login page."""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        # Get credentials from config
        admin_username = get_admin_username()
        admin_password_hash = get_admin_password_hash()

        if not admin_password_hash:
            flash(
                'Admin credentials are not configured. Set ADMIN_PASSWORD_HASH and restart the app.',
                'error')
            return render_template('admin/login.html')

        if username == admin_username and admin_password_hash and check_password_hash(admin_password_hash, password):
            session['admin_logged_in'] = True

            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = current_app.config.get(
                    'REMEMBER_COOKIE_DURATION', timedelta(days=30))
                session['remember_me'] = True
            else:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(minutes=30)
                session.pop('remember_me', None)

            return redirect(url_for('admin_dashboard.dashboard'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('admin/login.html')


@admin_auth_bp.route('/logout')
def logout() -> WerkzeugResponse:
    """Admin logout."""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_auth.login'))


@admin_auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password() -> str:
    """Password reset using recovery code or manual fallback."""
    remaining_codes = AdminRecoveryCode.get_remaining_count()
    
    if request.method == 'POST':
        recovery_code = request.form.get('recovery_code', '').strip()
        new_password = request.form.get('new_password', '')

        if not new_password:
            flash('Please enter a new password.', 'error')
            return render_template('admin/forgot_password.html', remaining_codes=remaining_codes)

        # Preferred: recovery code verification
        if recovery_code:
            if AdminRecoveryCode.verify_and_use(recovery_code):
                new_hash = generate_password_hash(new_password)
                updated_remaining = AdminRecoveryCode.get_remaining_count()

                flash(
                    'Recovery code verified! Update your .env file with the new password hash below.',
                    'success')
                flash(f'Remaining recovery codes: {updated_remaining}', 'info')

                return render_template(
                    'admin/forgot_password.html',
                    new_hash=new_hash,
                    remaining_codes=updated_remaining,
                    used_recovery_code=True
                )

            flash('Invalid or already used recovery code.', 'error')
            return render_template('admin/forgot_password.html', remaining_codes=remaining_codes)

        # Legacy fallback: manual hash generation
        if remaining_codes == 0:
            flash(
                'No recovery codes configured. Generated hash using legacy fallback mode.',
                'warning')
        else:
            flash(
                'Generated hash without a recovery code (legacy fallback mode).',
                'warning')
        flash('Set up recovery codes at /admin/security for stronger protection.', 'info')
        new_hash = generate_password_hash(new_password)
        return render_template(
            'admin/forgot_password.html',
            new_hash=new_hash,
            remaining_codes=remaining_codes,
            used_recovery_code=False
        )

    return render_template('admin/forgot_password.html', remaining_codes=remaining_codes)


@admin_auth_bp.route('/security', methods=['GET', 'POST'])
@login_required
def security_settings() -> str:
    """Security settings - generate recovery codes."""
    remaining_codes = AdminRecoveryCode.get_remaining_count()
    new_codes = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'generate_codes':
            # Generate new recovery codes
            new_codes = AdminRecoveryCode.generate_codes(10)
            remaining_codes = 10
            flash('New recovery codes generated! Save these codes securely - they will not be shown again.', 'warning')
    
    return render_template(
        'admin/security.html',
        remaining_codes=remaining_codes,
        new_codes=new_codes
    )
