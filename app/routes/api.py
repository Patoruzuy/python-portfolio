"""
API routes blueprint.
Handles: /api/projects, /api/blog, /api/contact, /api/newsletter.
"""
from flask import Blueprint, jsonify, request, flash, redirect, url_for, current_app, Response, Flask
from app.models import db, Project, BlogPost, Newsletter
from app.utils.rate_limiter import RATE_LIMITS
from datetime import datetime, timezone
from typing import Tuple

# Create API blueprint
api_bp = Blueprint('api', __name__)

# Endpoints that intentionally accept cross-origin-style POSTs without CSRF token.
# These are public API handlers consumed by JS clients and forms.
API_CSRF_EXEMPT_ENDPOINTS = (
    'api.api_contact',
    'api.api_newsletter_subscribe',
)


def get_limiter():
    """Get limiter from Flask app extensions."""
    return current_app.extensions.get('limiter')


def register_api_csrf_exemptions(app: Flask) -> None:
    """
    Apply Flask-WTF CSRF exemptions for selected API endpoints.

    Uses CSRFProtect.exempt(...) so Flask-WTF's internal registry is updated.
    """
    csrf = app.extensions.get('csrf')
    if not csrf:
        return

    for endpoint in API_CSRF_EXEMPT_ENDPOINTS:
        view_func = app.view_functions.get(endpoint)
        if view_func is not None:
            csrf.exempt(view_func)


def register_public_newsletter_routes(app: Flask) -> None:
    """
    Register non-/api newsletter confirm/unsubscribe aliases.

    Email templates point to /newsletter/... links for usability and backward
    compatibility, while API routes stay under /api.
    """
    confirm_view = app.view_functions.get('api.newsletter_confirm')
    if confirm_view is not None and 'newsletter_confirm' not in app.view_functions:
        app.add_url_rule(
            '/newsletter/confirm/<token>',
            endpoint='newsletter_confirm',
            view_func=confirm_view,
        )

    unsubscribe_view = app.view_functions.get('api.newsletter_unsubscribe')
    if unsubscribe_view is not None and 'newsletter_unsubscribe' not in app.view_functions:
        app.add_url_rule(
            '/newsletter/unsubscribe/<token>',
            endpoint='newsletter_unsubscribe',
            view_func=unsubscribe_view,
        )


@api_bp.route('/projects')
def api_projects() -> Response:
    """API endpoint for project filtering"""
    category = request.args.get('category')
    technology = request.args.get('technology')

    query = Project.query

    if category:
        query = query.filter_by(category=category)

    if technology:
        query = query.filter(Project.technologies.contains(technology))

    projects = query.all()

    result = []
    for p in projects:
        result.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'technologies': [t.strip() for t in p.technologies.split(',')] if p.technologies else [],
            'category': p.category,
            'image': p.image_url,
            'github': p.github_url,
            'demo': p.demo_url
        })

    return jsonify(result)


@api_bp.route('/blog')
def api_blog() -> Response:
    """API endpoint for blog filtering"""
    category = request.args.get('category')
    tag = request.args.get('tag')

    query = BlogPost.query.filter_by(published=True)

    if category:
        query = query.filter_by(category=category)

    if tag:
        query = query.filter(BlogPost.tags.contains(tag))

    posts = query.order_by(BlogPost.created_at.desc()).all()

    result = []
    for p in posts:
        result.append({
            'id': p.id,
            'slug': p.slug,
            'title': p.title,
            'excerpt': p.excerpt,
            'author': p.author,
            'category': p.category,
            'tags': p.tags,
            'image': p.image_url,
            'read_time': p.read_time,
            'date': p.created_at.strftime('%B %d, %Y'),
            'view_count': p.view_count
        })

    return jsonify(result)


@api_bp.route('/contact', methods=['POST'])
def api_contact() -> Tuple[Response, int]:
    """API endpoint for contact form submission with async email processing"""
    # Apply rate limiting
    limiter = get_limiter()
    if limiter:
        limiter.limit(RATE_LIMITS['api_contact'])(lambda: None)()
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()

        # Validate required fields
        required_fields = ['name', 'email', 'subject', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Import here to avoid circular import
        from app.tasks.email_tasks import send_contact_email

        # Queue email sending as async task (non-blocking)
        task = send_contact_email.delay({
            'name': data.get('name'),
            'email': data.get('email'),
            'subject': data.get('subject'),
            'message': data.get('message'),
            'projectType': data.get('projectType', 'Not specified')
        })

        # Return immediately (email will be sent asynchronously)
        return jsonify({
            'success': True,
            'message': 'Your message has been sent successfully!',
            'task_id': task.id  # Can be used to check task status later
        }), 200

    except Exception as e:
        print(f"Error queuing email task: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send message. Please try again later.'
        }), 500


@api_bp.route('/newsletter/subscribe', methods=['POST'])
def api_newsletter_subscribe() -> Tuple[Response, int]:
    """API endpoint for newsletter subscription"""
    # Apply rate limiting
    limiter = get_limiter()
    if limiter:
        limiter.limit(RATE_LIMITS['api_newsletter'])(lambda: None)()
    
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()

        email = data.get('email', '').strip()
        name = data.get('name', '').strip()

        # Validate email
        if not email or '@' not in email:
            return jsonify({
                'success': False,
                'error': 'Please provide a valid email address.'
            }), 400

        # Check if already subscribed
        existing = Newsletter.query.filter_by(email=email).first()
        if existing:
            if existing.active:
                return jsonify({
                    'success': False,
                    'error': 'This email is already subscribed to our newsletter.'
                }), 400
            else:
                # Reactivate subscription
                existing.active = True
                existing.unsubscribed_at = None
                db.session.commit()
                return jsonify({
                    'success': True,
                    'message': 'Welcome back! Your subscription has been reactivated.'
                }), 200

        # Create new subscription
        import secrets
        subscription = Newsletter(
            email=email,
            name=name if name else None,
            confirmation_token=secrets.token_urlsafe(32)
        )

        db.session.add(subscription)
        db.session.commit()

        # Send confirmation email via Celery
        from app.tasks.email_tasks import send_newsletter_confirmation
        try:
            send_newsletter_confirmation.delay(
                email, name, subscription.confirmation_token)
        except Exception as e:
            print(f"Error queueing confirmation email: {e}")

        return jsonify({
            'success': True,
            'message': f'🎉 Welcome aboard! Check your inbox at {email} to confirm your subscription.'
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Newsletter subscription error: {e}")
        return jsonify({
            'success': False,
            'error': 'Subscription failed. Please try again later.'
        }), 500


# Newsletter confirmation/unsubscribe routes (not under /api prefix)
@api_bp.route('/newsletter/confirm/<token>')
def newsletter_confirm(token: str) -> Response:
    """Confirm newsletter subscription"""
    try:
        subscription = Newsletter.query.filter_by(
            confirmation_token=token).first()

        if not subscription:
            flash('Invalid confirmation link.', 'error')
            return redirect(url_for('public.blog'))

        if subscription.confirmed:
            flash('Your subscription is already confirmed!', 'info')
            return redirect(url_for('public.blog'))

        subscription.confirmed = True
        db.session.commit()

        flash(
            '🎉 Subscription confirmed! You will now receive our newsletter.',
            'success')
        return redirect(url_for('public.blog'))

    except Exception as e:
        print(f"Newsletter confirmation error: {e}")
        flash('Confirmation failed. Please try again.', 'error')
        return redirect(url_for('public.blog'))


@api_bp.route('/newsletter/unsubscribe/<token>')
def newsletter_unsubscribe(token: str) -> Response:
    """Unsubscribe from newsletter"""
    try:
        subscription = Newsletter.query.filter_by(
            confirmation_token=token).first()

        if not subscription:
            flash('Invalid unsubscribe link.', 'error')
            return redirect(url_for('public.blog'))

        if not subscription.active:
            flash('You are already unsubscribed.', 'info')
            return redirect(url_for('public.blog'))

        subscription.active = False
        subscription.unsubscribed_at = datetime.now(timezone.utc)
        db.session.commit()

        flash('You have been unsubscribed from the newsletter.', 'info')
        return redirect(url_for('public.blog'))

    except Exception as e:
        print(f"Newsletter unsubscribe error: {e}")
        flash('Unsubscribe failed. Please try again.', 'error')
        return redirect(url_for('public.blog'))
