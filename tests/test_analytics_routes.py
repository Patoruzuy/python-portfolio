"""
Tests for Analytics routes (dashboard and event tracking).
"""
from app.models import db, Newsletter, AnalyticsEvent
from unittest.mock import patch


class TestAnalyticsDashboard:
    """Test analytics dashboard page."""
    
    def test_analytics_dashboard_requires_auth(self, client):
        """Test that analytics dashboard requires authentication."""
        response = client.get('/admin/analytics')
        
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]
    
    def test_analytics_dashboard_route_calls_utils(self, auth_client, database):
        """Test analytics dashboard route calls utility functions."""
        client = auth_client
        
        # Create sample newsletter data for the route
        newsletter = Newsletter(
            email='test@example.com',
            active=True,
            confirmed=True,
            confirmation_token='token123'
        )
        db.session.add(newsletter)
        db.session.commit()
        
        # Mock analytics utilities and database queries
        with patch('app.utils.analytics_utils.get_analytics_summary') as mock_summary, \
             patch('app.utils.analytics_utils.get_daily_traffic') as mock_traffic:
            
            mock_summary.return_value = {
                'total_views': 100,
                'unique_sessions': 50,
                'avg_pages_per_session': 2.0,
                'popular_pages': [],
                'referrer_stats': [],
                'device_stats': {},
                'browser_stats': {},
                'new_visitors': 30,
                'returning_visitors': 20,
            }
            mock_traffic.return_value = [
                {'date': '2024-01-01', 'views': 10},
                {'date': '2024-01-02', 'views': 15}
            ]
            
            response = client.get('/admin/analytics')
            
            assert response.status_code == 200
            # Verify utility functions were called with default 30 days
            mock_summary.assert_called_once_with(30)
            mock_traffic.assert_called_once_with(30)
    
    def test_analytics_dashboard_accepts_days_parameter(self, auth_client, database):
        """Test analytics dashboard accepts days query parameter."""
        client = auth_client
        
        # Create sample newsletter data
        newsletter = Newsletter(
            email='test2@example.com',
            active=True,
            confirmed=True,
            confirmation_token='token456'
        )
        db.session.add(newsletter)
        db.session.commit()
        
        with patch('app.utils.analytics_utils.get_analytics_summary') as mock_summary, \
             patch('app.utils.analytics_utils.get_daily_traffic') as mock_traffic:
            
            mock_summary.return_value = {
                'total_views': 100,
                'unique_sessions': 50,
                'avg_pages_per_session': 2.0,
                'popular_pages': [],
                'referrer_stats': [],
                'device_stats': {},
                'browser_stats': {},
                'new_visitors': 30,
                'returning_visitors': 20,
            }
            mock_traffic.return_value = []
            
            response = client.get('/admin/analytics?days=7')
            
            assert response.status_code == 200
            # Verify the function was called with days=7
            mock_summary.assert_called_once_with(7)
            mock_traffic.assert_called_once_with(7)

    def test_analytics_dashboard_handles_empty_newsletter_table(self, auth_client, database):
        """Analytics dashboard should not fail when newsletter table is empty."""
        client = auth_client
        Newsletter.query.delete()
        db.session.commit()

        with patch('app.utils.analytics_utils.get_analytics_summary') as mock_summary, \
             patch('app.utils.analytics_utils.get_daily_traffic') as mock_traffic:
            mock_summary.return_value = {
                'total_views': 0,
                'unique_sessions': 0,
                'avg_pages_per_session': 0,
                'popular_pages': [],
                'referrer_stats': [],
                'device_stats': {},
                'browser_stats': {},
                'new_visitors': 0,
                'returning_visitors': 0,
            }
            mock_traffic.return_value = []

            response = client.get('/admin/analytics')

            assert response.status_code == 200


class TestEventTracking:
    """Test analytics event tracking endpoint."""
    
    def test_track_event_success(self, client, database):
        """Test successful event tracking."""
        session_id = 'track-test-session'
        client.set_cookie('analytics_session', session_id)
        
        with patch('app.utils.analytics_utils.track_event') as mock_track:
            mock_track.return_value = AnalyticsEvent(
                session_id=session_id,
                event_type='click',
                event_name='test-button'
            )
            
            data = {
                'event_type': 'click',
                'event_name': 'test-button',
                'page_path': '/test-page',
                'element_id': 'btn-submit',
                'metadata': {'action': 'form-submit'}
            }
            
            response = client.post(
                '/api/analytics/event',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 201
            assert response.json['success'] is True
            
            # Verify track_event was called with correct params
            mock_track.assert_called_once_with(
                session_id=session_id,
                event_type='click',
                event_name='test-button',
                page_path='/test-page',
                element_id='btn-submit',
                metadata={'action': 'form-submit'}
            )
    
    def test_track_event_no_session(self, client):
        """Test event tracking fails without session cookie."""
        data = {
            'event_type': 'click',
            'event_name': 'test-button'
        }
        
        response = client.post(
            '/api/analytics/event',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        assert response.json['success'] is False
        assert 'No session' in response.json['error']
    
    def test_track_event_handles_tracking_failure(self, client):
        """Test event tracking handles failures gracefully."""
        client.set_cookie('analytics_session', 'test-session')
        
        with patch('app.utils.analytics_utils.track_event') as mock_track:
            mock_track.return_value = None  # Simulate tracking failure
            
            data = {
                'event_type': 'click',
                'event_name': 'test-button'
            }
            
            response = client.post(
                '/api/analytics/event',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 500
            assert response.json['success'] is False
            assert 'Tracking failed' in response.json['error']
    
    def test_track_event_handles_exceptions(self, client):
        """Test event tracking handles exceptions gracefully."""
        client.set_cookie('analytics_session', 'test-session')
        
        with patch('app.utils.analytics_utils.track_event') as mock_track:
            mock_track.side_effect = Exception('Database error')
            
            data = {
                'event_type': 'click',
                'event_name': 'test-button'
            }
            
            response = client.post(
                '/api/analytics/event',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 500
            assert response.json['success'] is False
    
    def test_track_event_accepts_minimal_data(self, client):
        """Test event tracking works with minimal required data."""
        client.set_cookie('analytics_session', 'test-session')
        
        with patch('app.utils.analytics_utils.track_event') as mock_track:
            mock_track.return_value = AnalyticsEvent(
                session_id='test-session',
                event_type='pageview'
            )
            
            # Minimal data - only event_type
            data = {'event_type': 'pageview'}
            
            response = client.post(
                '/api/analytics/event',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 201
            assert response.json['success'] is True
    
    def test_track_event_with_metadata(self, client):
        """Test event tracking preserves metadata."""
        client.set_cookie('analytics_session', 'test-session')
        
        with patch('app.utils.analytics_utils.track_event') as mock_track:
            mock_track.return_value = AnalyticsEvent(session_id='test-session')
            
            metadata = {
                'button_text': 'Click Me',
                'form_id': 'contact-form',
                'position': {'x': 100, 'y': 200}
            }
            
            data = {
                'event_type': 'click',
                'event_name': 'form-button',
                'metadata': metadata
            }
            
            response = client.post(
                '/api/analytics/event',
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 201
            
            # Verify metadata was passed correctly
            call_args = mock_track.call_args
            assert call_args[1]['metadata'] == metadata
