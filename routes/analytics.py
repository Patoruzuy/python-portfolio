"""
Analytics routes blueprint.
Handles: /admin/analytics, /api/analytics/event.
"""
from flask import Blueprint, render_template, jsonify, request, Response
from models import db, BlogPost, Newsletter, AnalyticsEvent
from utils.analytics_utils import get_analytics_summary, get_daily_traffic, track_event
from routes.admin.utils import login_required
from typing import Tuple

# Create analytics blueprint
analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/admin/analytics')
@login_required
def analytics_dashboard() -> str:
    """Analytics dashboard page - shows traffic and user behavior metrics"""
    # Get analytics period from query param (default 30 days)
    days = request.args.get('days', 30, type=int)
    
    # Get analytics summary
    summary = get_analytics_summary(days)
    
    # Get daily traffic for chart
    daily_traffic = get_daily_traffic(days)
    
    # Get newsletter stats
    total_subscribers = Newsletter.query.filter_by(active=True, confirmed=True).count()
    unconfirmed = Newsletter.query.filter_by(active=True, confirmed=False).count()
    unsubscribed = Newsletter.query.filter_by(active=False).count()
    
    # Get blog post stats
    blog_stats = db.session.query(
        BlogPost.title,
        BlogPost.slug,
        BlogPost.view_count
    ).filter(
        BlogPost.published == True  # noqa: E712
    ).order_by(BlogPost.view_count.desc()).limit(10).all()
    
    # Get recent events
    recent_events = AnalyticsEvent.query.order_by(
        AnalyticsEvent.created_at.desc()
    ).limit(20).all()
    
    return render_template('admin/analytics.html',
                          summary=summary,
                          daily_traffic=daily_traffic,
                          days=days,
                          newsletter_stats={
                              'subscribers': total_subscribers,
                              'unconfirmed': unconfirmed,
                              'unsubscribed': unsubscribed
                          },
                          blog_stats=blog_stats,
                          recent_events=recent_events)


@analytics_bp.route('/api/analytics/event', methods=['POST'])
def track_analytics_event() -> Tuple[Response, int]:
    """API endpoint for tracking custom analytics events from JavaScript"""
    try:
        data = request.json
        session_id = request.cookies.get('analytics_session')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No session'}), 400
        
        event = track_event(
            session_id=session_id,
            event_type=data.get('event_type'),
            event_name=data.get('event_name'),
            page_path=data.get('page_path'),
            element_id=data.get('element_id'),
            metadata=data.get('metadata')
        )
        
        if event:
            return jsonify({'success': True}), 201
        else:
            return jsonify({'success': False, 'error': 'Tracking failed'}), 500
            
    except Exception as e:
        print(f"Event tracking error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
