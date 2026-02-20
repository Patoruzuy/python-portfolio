"""
GDPR and privacy routes blueprint.
Handles: /privacy-policy, /my-data, /api/cookie-consent, /api/my-data/*.
"""
from flask import Blueprint, render_template, jsonify, request, send_file, Response
from models import db, PageView, AnalyticsEvent, UserSession, CookieConsent
from datetime import datetime, timezone
from typing import Tuple, Union
import json
from io import BytesIO

# Create GDPR blueprint
gdpr_bp = Blueprint('gdpr', __name__)


@gdpr_bp.route('/privacy-policy')
def privacy_policy() -> str:
    """Privacy policy and cookie information"""
    return render_template('privacy_policy.html')


@gdpr_bp.route('/my-data')
def my_data_page() -> str:
    """Page for users to view and download their data"""
    return render_template('my_data.html')


@gdpr_bp.route('/api/cookie-consent', methods=['POST'])
def log_cookie_consent() -> Tuple[Response, int]:
    """Log cookie consent decisions for GDPR compliance audit trail"""
    try:
        data = request.json
        if data is None:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        session_id = request.cookies.get('analytics_session') or data.get('session_id')
        
        consent_log = CookieConsent(
            session_id=session_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:300],
            consent_type=data.get('consent_type', 'accepted'),
            categories_accepted=data.get('categories', ['necessary', 'analytics'])
        )
        
        db.session.add(consent_log)
        db.session.commit()
        
        return jsonify({'success': True}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Cookie consent logging error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@gdpr_bp.route('/api/my-data/download')
def download_my_data() -> Union[Response, Tuple[Response, int]]:
    """Export user's analytics data (GDPR data portability right)"""
    try:
        session_id = request.cookies.get('analytics_session')
        
        if not session_id:
            return jsonify({'error': 'No session found'}), 404
        
        # Collect user's data
        user_data: dict = {
            'session_id': session_id,
            'export_date': datetime.now(timezone.utc).isoformat(),
            'page_views': [],
            'events': [],
            'consent_history': []
        }
        
        # Get page views
        page_views = PageView.query.filter_by(session_id=session_id).all()
        for pv in page_views:
            user_data['page_views'].append({
                'path': pv.path,
                'timestamp': pv.created_at.isoformat() if pv.created_at else None,
                'referrer': pv.referrer,
                'device_type': pv.device_type,
                'browser': pv.browser,
                'os': pv.os
            })
        
        # Get events
        events = AnalyticsEvent.query.filter_by(session_id=session_id).all()
        for event in events:
            user_data['events'].append({
                'event_type': event.event_type,
                'event_name': event.event_name,
                'timestamp': event.created_at.isoformat() if event.created_at else None,
                'page_path': event.page_path
            })
        
        # Get consent history
        consents = CookieConsent.query.filter_by(session_id=session_id).all()
        for consent in consents:
            user_data['consent_history'].append({
                'consent_type': consent.consent_type,
                'categories': consent.categories_accepted,
                'timestamp': consent.created_at.isoformat() if consent.created_at else None
            })
        
        # Create JSON file
        json_data = json.dumps(user_data, indent=2)
        buffer = BytesIO()
        buffer.write(json_data.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'my_data_{session_id[:8]}.json'
        )
        
    except Exception as e:
        print(f"Data export error: {e}")
        return jsonify({'error': 'Export failed'}), 500


@gdpr_bp.route('/api/my-data/delete', methods=['POST'])
def delete_my_data() -> Tuple[Response, int]:
    """Delete user's analytics data (GDPR right to erasure)"""
    try:
        session_id = request.cookies.get('analytics_session')
        
        if not session_id:
            return jsonify({'error': 'No session found'}), 404
        
        # Delete page views
        PageView.query.filter_by(session_id=session_id).delete()
        
        # Delete events
        AnalyticsEvent.query.filter_by(session_id=session_id).delete()
        
        # Delete user session
        UserSession.query.filter_by(session_id=session_id).delete()
        
        # Keep consent log for compliance (required by law)
        # CookieConsent records are not deleted
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Your data has been deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Data deletion error: {e}")
        return jsonify({'error': 'Deletion failed'}), 500
