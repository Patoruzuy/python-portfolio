"""
Tests for GDPR routes (privacy policy, data download, data deletion).
"""
import pytest
import json
from datetime import datetime, timedelta
from models import db, PageView, AnalyticsEvent, CookieConsent, UserSession


class TestGDPRPages:
    """Test GDPR-related page rendering."""
    
    def test_privacy_policy_page_loads(self, client):
        """Test that privacy policy page loads successfully."""
        response = client.get('/privacy-policy')
        
        assert response.status_code == 200
        assert b'Privacy Policy' in response.data or b'privacy' in response.data.lower()
    
    def test_my_data_page_loads(self, client):
        """Test that my data page loads successfully."""
        response = client.get('/my-data')
        
        assert response.status_code == 200


class TestCookieConsent:
    """Test cookie consent logging endpoint."""
    
    def test_log_cookie_consent_success(self, client, database):
        """Test successful cookie consent logging."""
        client.set_cookie('analytics_session', 'test-session-123')
        
        data = {
            'consent_type': 'accepted',
            'categories': ['necessary', 'analytics', 'marketing']
        }
        
        response = client.post(
            '/api/cookie-consent',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        assert response.json['success'] is True
        
        # Verify consent was logged
        consent = CookieConsent.query.filter_by(session_id='test-session-123').first()
        assert consent is not None
        assert consent.consent_type == 'accepted'
        assert 'analytics' in consent.categories_accepted
    
    def test_log_cookie_consent_with_session_id_in_body(self, client, database):
        """Test consent logging when session_id is in request body."""
        data = {
            'session_id': 'body-session-456',
            'consent_type': 'rejected',
            'categories': ['necessary']
        }
        
        response = client.post(
            '/api/cookie-consent',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 201
        assert response.json['success'] is True
        
        consent = CookieConsent.query.filter_by(session_id='body-session-456').first()
        assert consent is not None
        assert consent.consent_type == 'rejected'
    
    def test_log_cookie_consent_no_json_data(self, client):
        """Test consent logging fails without JSON data."""
        response = client.post('/api/cookie-consent')
        
        # Flask returns 415 error which gets caught and returns 500
        assert response.status_code == 500
        assert response.json['success'] is False
    
    def test_log_cookie_consent_stores_ip_and_user_agent(self, client, database):
        """Test that consent logging captures IP and user agent."""
        client.set_cookie('analytics_session', 'test-session-789')
        
        data = {'consent_type': 'accepted', 'categories': ['necessary']}
        
        response = client.post(
            '/api/cookie-consent',
            json=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'TestBrowser/1.0'
            }
        )
        
        assert response.status_code == 201
        
        consent = CookieConsent.query.filter_by(session_id='test-session-789').first()
        assert consent is not None
        assert consent.user_agent == 'TestBrowser/1.0'
        assert consent.ip_address is not None


class TestMyDataDownload:
    """Test GDPR data portability (data download)."""
    
    def test_download_my_data_success(self, client, database):
        """Test successful data export."""
        session_id = 'download-test-session'
        client.set_cookie('analytics_session', session_id)
        
        # Create sample data for this session
        page_view = PageView(
            session_id=session_id,
            path='/test-page',
            referrer='https://example.com',
            device_type='desktop',
            browser='Chrome',
            os='Windows'
        )
        db.session.add(page_view)
        
        event = AnalyticsEvent(
            session_id=session_id,
            event_type='click',
            event_name='test-button',
            page_path='/test-page'
        )
        db.session.add(event)
        
        consent = CookieConsent(
            session_id=session_id,
            consent_type='accepted',
            categories_accepted=['necessary', 'analytics']
        )
        db.session.add(consent)
        
        db.session.commit()
        
        # Download data
        response = client.get('/api/my-data/download')
        
        assert response.status_code == 200
        assert response.mimetype == 'application/json'
        assert 'attachment' in response.headers.get('Content-Disposition', '')
        
        # Parse downloaded JSON
        data = json.loads(response.data)
        
        assert data['session_id'] == session_id
        assert 'export_date' in data
        assert len(data['page_views']) == 1
        assert data['page_views'][0]['path'] == '/test-page'
        assert len(data['events']) == 1
        assert data['events'][0]['event_name'] == 'test-button'
        assert len(data['consent_history']) == 1
        assert data['consent_history'][0]['consent_type'] == 'accepted'
    
    def test_download_my_data_no_session(self, client):
        """Test data download fails without session cookie."""
        response = client.get('/api/my-data/download')
        
        assert response.status_code == 404
        assert response.json['error'] == 'No session found'
    
    def test_download_my_data_empty_session(self, client, database):
        """Test data download with session but no data."""
        session_id = 'empty-session'
        client.set_cookie('analytics_session', session_id)
        
        response = client.get('/api/my-data/download')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['session_id'] == session_id
        assert len(data['page_views']) == 0
        assert len(data['events']) == 0
        assert len(data['consent_history']) == 0
    
    def test_download_my_data_includes_multiple_records(self, client, database):
        """Test data download includes all user's records."""
        session_id = 'multi-record-session'
        client.set_cookie('analytics_session', session_id)
        
        # Create multiple page views
        for i in range(3):
            pv = PageView(
                session_id=session_id,
                path=f'/page-{i}',
                device_type='mobile'
            )
            db.session.add(pv)
        
        # Create multiple events
        for i in range(2):
            event = AnalyticsEvent(
                session_id=session_id,
                event_type='click',
                event_name=f'button-{i}',
                page_path='/test'
            )
            db.session.add(event)
        
        db.session.commit()
        
        response = client.get('/api/my-data/download')
        data = json.loads(response.data)
        
        assert len(data['page_views']) == 3
        assert len(data['events']) == 2


class TestMyDataDeletion:
    """Test GDPR right to erasure (data deletion)."""
    
    def test_delete_my_data_success(self, client, database):
        """Test successful data deletion."""
        session_id = 'delete-test-session'
        client.set_cookie('analytics_session', session_id)
        
        # Create data to delete
        page_view = PageView(session_id=session_id, path='/test')
        event = AnalyticsEvent(session_id=session_id, event_type='click', event_name='test')
        user_session = UserSession(session_id=session_id)
        consent = CookieConsent(session_id=session_id, consent_type='accepted', categories_accepted=['necessary'])
        
        db.session.add_all([page_view, event, user_session, consent])
        db.session.commit()
        
        # Verify data exists
        assert PageView.query.filter_by(session_id=session_id).count() == 1
        assert AnalyticsEvent.query.filter_by(session_id=session_id).count() == 1
        assert UserSession.query.filter_by(session_id=session_id).count() == 1
        assert CookieConsent.query.filter_by(session_id=session_id).count() == 1
        
        # Delete data
        response = client.post('/api/my-data/delete')
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'deleted' in response.json['message'].lower()
        
        # Verify analytics data deleted
        assert PageView.query.filter_by(session_id=session_id).count() == 0
        assert AnalyticsEvent.query.filter_by(session_id=session_id).count() == 0
        assert UserSession.query.filter_by(session_id=session_id).count() == 0
        
        # Verify consent log preserved (required by law)
        assert CookieConsent.query.filter_by(session_id=session_id).count() == 1
    
    def test_delete_my_data_no_session(self, client):
        """Test data deletion fails without session cookie."""
        response = client.post('/api/my-data/delete')
        
        assert response.status_code == 404
        assert response.json['error'] == 'No session found'
    
    def test_delete_my_data_preserves_other_sessions(self, client, database):
        """Test deletion only affects the user's session."""
        session_id_1 = 'delete-session-1'
        session_id_2 = 'preserve-session-2'
        
        # Create data for both sessions
        pv1 = PageView(session_id=session_id_1, path='/delete-me')
        pv2 = PageView(session_id=session_id_2, path='/keep-me')
        
        db.session.add_all([pv1, pv2])
        db.session.commit()
        
        # Delete session 1
        client.set_cookie('analytics_session', session_id_1)
        response = client.post('/api/my-data/delete')
        
        assert response.status_code == 200
        
        # Verify session 1 deleted, session 2 preserved
        assert PageView.query.filter_by(session_id=session_id_1).count() == 0
        assert PageView.query.filter_by(session_id=session_id_2).count() == 1
    
    def test_delete_my_data_handles_empty_session(self, client, database):
        """Test deletion succeeds even if no data exists."""
        session_id = 'empty-delete-session'
        client.set_cookie('analytics_session', session_id)
        
        response = client.post('/api/my-data/delete')
        
        assert response.status_code == 200
        assert response.json['success'] is True
