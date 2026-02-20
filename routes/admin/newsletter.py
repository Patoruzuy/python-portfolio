"""
Admin newsletter management routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.wrappers.response import Response as WerkzeugResponse
from models import db, Newsletter
from routes.admin.utils import login_required

# Create admin newsletter blueprint
admin_newsletter_bp = Blueprint('admin_newsletter', __name__, url_prefix='/admin')


@admin_newsletter_bp.route('/newsletter')
@login_required
def newsletter() -> str:
    """View newsletter subscribers."""
    subscribers = Newsletter.query.order_by(
        Newsletter.subscribed_at.desc()).all()
    active_count = Newsletter.query.filter_by(active=True).count()
    total_count = Newsletter.query.count()

    return render_template('admin/newsletter.html',
                           subscribers=subscribers,
                           active_count=active_count,
                           total_count=total_count)


@admin_newsletter_bp.route('/newsletter/delete/<int:subscriber_id>', methods=['POST'])
@login_required
def delete_subscriber(subscriber_id: int) -> WerkzeugResponse:
    """Delete a newsletter subscriber."""
    subscriber = Newsletter.query.get_or_404(subscriber_id)
    db.session.delete(subscriber)
    db.session.commit()

    flash('Subscriber deleted successfully!', 'success')
    return redirect(url_for('admin_newsletter.newsletter'))
