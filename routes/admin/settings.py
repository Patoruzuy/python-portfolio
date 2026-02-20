"""
Admin settings and configuration routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.wrappers.response import Response as WerkzeugResponse
from typing import Union, Tuple
import json
from datetime import datetime
from models import db, OwnerProfile, SiteConfig
from routes.admin.utils import login_required

# Create admin settings blueprint
admin_settings_bp = Blueprint('admin_settings', __name__, url_prefix='/admin')


@admin_settings_bp.route('/owner-profile', methods=['GET', 'POST'])
@login_required
def owner_profile() -> Union[str, WerkzeugResponse]:
    """Edit owner profile information."""
    owner = OwnerProfile.query.first()

    if not owner:
        # Create default profile if none exists
        owner = OwnerProfile(
            name="Portfolio Owner",
            title="Developer",
            email="contact@example.com"
        )
        db.session.add(owner)
        db.session.commit()

    if request.method == 'POST':
        owner.name = request.form.get('name')
        owner.title = request.form.get('title')
        owner.bio = request.form.get('bio')
        owner.email = request.form.get('email')
        owner.phone = request.form.get('phone')
        owner.location = request.form.get('location')
        owner.github = request.form.get('github')
        owner.linkedin = request.form.get('linkedin')
        owner.twitter = request.form.get('twitter')
        owner.profile_image = request.form.get('profile_image') or owner.profile_image

        # About page content
        owner.intro = request.form.get('intro')
        owner.summary = request.form.get('summary')
        owner.journey = request.form.get('journey')
        owner.interests = request.form.get('interests')

        # Stats
        try:
            owner.years_experience = int(request.form.get('years_experience', 0))
            owner.projects_completed = int(request.form.get('projects_completed', 0))
            owner.contributions = int(request.form.get('contributions', 0))
            owner.clients_served = int(request.form.get('clients_served', 0))
            owner.certifications = int(request.form.get('certifications', 0))
        except ValueError:
            flash('Invalid numeric value for stats', 'error')
            return render_template('admin/owner_profile.html', owner=owner)

        # JSON fields - validate JSON format
        try:
            skills_data = request.form.get('skills_json', '[]')
            json.loads(skills_data)  # Validate
            owner.skills_json = skills_data

            exp_data = request.form.get('experience_json', '[]')
            json.loads(exp_data)  # Validate
            owner.experience_json = exp_data

            expertise_data = request.form.get('expertise_json', '[]')
            json.loads(expertise_data)  # Validate
            owner.expertise_json = expertise_data
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON format: {e}', 'error')
            return render_template('admin/owner_profile.html', owner=owner)

        db.session.commit()
        flash('Owner profile updated successfully!', 'success')
        return redirect(url_for('admin_settings.owner_profile'))

    return render_template('admin/owner_profile.html', owner=owner)


@admin_settings_bp.route('/site-config', methods=['GET', 'POST'])
@login_required
def site_config() -> Union[str, WerkzeugResponse]:
    """Edit site configuration."""
    config = SiteConfig.query.first()

    if not config:
        config = SiteConfig(
            site_name="Developer Portfolio",
            blog_enabled=True,
            products_enabled=True
        )
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
        config.site_name = request.form.get('site_name')
        config.tagline = request.form.get('tagline')

        # Email settings
        config.mail_server = request.form.get('mail_server')
        try:
            config.mail_port = int(request.form.get('mail_port', 587))
        except ValueError:
            config.mail_port = 587
        config.mail_use_tls = request.form.get('mail_use_tls') == 'on'
        config.mail_username = request.form.get('mail_username')
        config.mail_default_sender = request.form.get('mail_default_sender')
        config.mail_recipient = request.form.get('mail_recipient')

        # Feature flags
        config.blog_enabled = request.form.get('blog_enabled') == 'on'
        config.products_enabled = request.form.get('products_enabled') == 'on'
        config.analytics_enabled = request.form.get('analytics_enabled') == 'on'

        db.session.commit()

        # Reload email config in app
        try:
            from app import configure_email_from_db
            configure_email_from_db()
            flash('Site configuration updated successfully! Email settings reloaded.', 'success')
        except ImportError:
            flash('Site configuration updated successfully!', 'success')

        return redirect(url_for('admin_settings.site_config'))

    return render_template('admin/site_config.html', config=config)


@admin_settings_bp.route('/export-config')
@login_required
def export_config() -> WerkzeugResponse:
    """Export site configuration and owner profile as JSON."""
    owner = OwnerProfile.query.first()
    config = SiteConfig.query.first()

    export_data = {
        'exported_at': datetime.now().isoformat(),
        'owner_profile': {
            'name': owner.name if owner else None,
            'title': owner.title if owner else None,
            'bio': owner.bio if owner else None,
            'email': owner.email if owner else None,
            'phone': owner.phone if owner else None,
            'location': owner.location if owner else None,
            'github': owner.github if owner else None,
            'linkedin': owner.linkedin if owner else None,
            'twitter': owner.twitter if owner else None,
            'profile_image': owner.profile_image if owner else None,
            'years_experience': owner.years_experience if owner else 0,
            'projects_completed': owner.projects_completed if owner else 0,
            'contributions': owner.contributions if owner else 0,
            'clients_served': owner.clients_served if owner else 0,
            'certifications': owner.certifications if owner else 0,
            'skills': owner.skills if owner else [],
            'experience': owner.experience if owner else [],
            'expertise': owner.expertise if owner else []
        },
        'site_config': {
            'site_name': config.site_name if config else None,
            'tagline': config.tagline if config else None,
            'mail_server': config.mail_server if config else None,
            'mail_port': config.mail_port if config else None,
            'mail_use_tls': config.mail_use_tls if config else None,
            'mail_username': config.mail_username if config else None,
            'mail_default_sender': config.mail_default_sender if config else None,
            'mail_recipient': config.mail_recipient if config else None,
            'blog_enabled': config.blog_enabled if config else True,
            'products_enabled': config.products_enabled if config else True,
            'analytics_enabled': config.analytics_enabled if config else False
        }
    }

    return jsonify(export_data)


@admin_settings_bp.route('/import-config', methods=['POST'])
@login_required
def import_config() -> Union[WerkzeugResponse, Tuple[WerkzeugResponse, int]]:
    """Import site configuration and owner profile from JSON."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            config_data = request.form.get('config_data')
            if not config_data:
                return jsonify({'success': False, 'error': 'No configuration data provided'}), 400
            data = json.loads(config_data)

        # Update owner profile
        if 'owner_profile' in data:
            owner = OwnerProfile.query.first()
            if not owner:
                owner = OwnerProfile()
                db.session.add(owner)

            op_data = data['owner_profile']
            owner.name = op_data.get('name')
            owner.title = op_data.get('title')
            owner.bio = op_data.get('bio')
            owner.email = op_data.get('email')
            owner.phone = op_data.get('phone')
            owner.location = op_data.get('location')
            owner.github = op_data.get('github')
            owner.linkedin = op_data.get('linkedin')
            owner.twitter = op_data.get('twitter')
            owner.profile_image = op_data.get('profile_image')
            owner.years_experience = op_data.get('years_experience', 0)
            owner.projects_completed = op_data.get('projects_completed', 0)
            owner.contributions = op_data.get('contributions', 0)
            owner.clients_served = op_data.get('clients_served', 0)
            owner.certifications = op_data.get('certifications', 0)
            owner.skills_json = json.dumps(op_data.get('skills', []))
            owner.experience_json = json.dumps(op_data.get('experience', []))
            owner.expertise_json = json.dumps(op_data.get('expertise', []))

        # Update site config
        if 'site_config' in data:
            config = SiteConfig.query.first()
            if not config:
                config = SiteConfig()
                db.session.add(config)

            sc_data = data['site_config']
            config.site_name = sc_data.get('site_name')
            config.tagline = sc_data.get('tagline')
            config.mail_server = sc_data.get('mail_server')
            config.mail_port = sc_data.get('mail_port')
            config.mail_use_tls = sc_data.get('mail_use_tls')
            config.mail_username = sc_data.get('mail_username')
            config.mail_default_sender = sc_data.get('mail_default_sender')
            config.mail_recipient = sc_data.get('mail_recipient')
            config.blog_enabled = sc_data.get('blog_enabled', True)
            config.products_enabled = sc_data.get('products_enabled', True)
            config.analytics_enabled = sc_data.get('analytics_enabled', False)

        db.session.commit()

        flash('Configuration imported successfully!', 'success')
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        flash(f'Import failed: {e}', 'error')
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_settings_bp.route('/contact-info', methods=['GET', 'POST'])
@login_required
def contact_info() -> WerkzeugResponse:
    """Legacy route - redirects to owner profile."""
    return redirect(url_for('admin_settings.owner_profile'))


@admin_settings_bp.route('/about-info', methods=['GET', 'POST'])
@login_required
def about_info() -> WerkzeugResponse:
    """Legacy route - redirects to owner profile."""
    return redirect(url_for('admin_settings.owner_profile'))
