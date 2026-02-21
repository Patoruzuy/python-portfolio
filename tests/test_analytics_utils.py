"""
Tests for analytics utility functions.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from app.utils.analytics_utils import (
    parse_user_agent,
    get_or_create_session,
    track_event,
    get_analytics_summary,
    get_daily_traffic
)
from app.models import UserSession, PageView, AnalyticsEvent, db


class TestParseUserAgent:
    """Test user agent parsing."""
    
    def test_parse_desktop_chrome(self):
        """Should parse desktop Chrome user agent."""
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        result = parse_user_agent(ua)
        
        assert result['device_type'] == 'desktop'
        assert 'Chrome' in result['browser']
        assert 'Windows' in result['os']
    
    def test_parse_mobile_safari(self):
        """Should parse mobile Safari user agent."""
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        result = parse_user_agent(ua)
        
        assert result['device_type'] == 'mobile'
        assert 'Safari' in result['browser'] or 'Mobile Safari' in result['browser']
        assert 'iOS' in result['os']
    
    def test_parse_tablet_ipad(self):
        """Should parse tablet iPad user agent."""
        ua = 'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
        result = parse_user_agent(ua)
        
        assert result['device_type'] == 'tablet'
        assert 'Safari' in result['browser'] or 'Mobile Safari' in result['browser']
    
    def test_parse_firefox_linux(self):
        """Should parse Firefox on Linux."""
        ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0'
        result = parse_user_agent(ua)
        
        assert result['device_type'] == 'desktop'
        assert 'Firefox' in result['browser']
        assert 'Linux' in result['os']
    
    def test_parse_empty_user_agent(self):
        """Should handle empty user agent string."""
        result = parse_user_agent('')
        
        assert result['device_type'] == 'unknown'
        assert result['browser'] == 'unknown'
        assert result['os'] == 'unknown'
    
    def test_parse_none_user_agent(self):
        """Should handle None user agent."""
        result = parse_user_agent(None)
        
        assert result['device_type'] == 'unknown'
        assert result['browser'] == 'unknown'
        assert result['os'] == 'unknown'
    
    def test_browser_length_limit(self):
        """Should limit browser string to 50 characters."""
        # Create a very long user agent
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) VeryLongBrowserNameThatExceeds50CharactersForTesting/1.0.0.0'
        result = parse_user_agent(ua)
        
        assert len(result['browser']) <= 50
    
    def test_os_length_limit(self):
        """Should limit OS string to 50 characters."""
        ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        result = parse_user_agent(ua)
        
        assert len(result['os']) <= 50


class TestGetOrCreateSession:
    """Test session management."""
    
    def test_creates_new_session(self, app, database):
        """Should create new session if not exists."""
        with app.test_request_context(
            '/',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0'},
            environ_base={'REMOTE_ADDR': '127.0.0.1'}
        ):
            from flask import request
            session = get_or_create_session('test_session_123', request)
            
            assert session is not None
            assert session.session_id == 'test_session_123'
            assert session.ip_address == '127.0.0.1'
            assert session.device_type == 'desktop'
            assert session.page_count == 1
    
    def test_returns_existing_session(self, app, database):
        """Should return existing session if found."""
        # Create initial session
        with app.test_request_context(
            '/',
            headers={'User-Agent': 'Mozilla/5.0 Chrome/119.0.0.0'},
            environ_base={'REMOTE_ADDR': '127.0.0.1'}
        ):
            from flask import request
            session1 = get_or_create_session('test_session_456', request)
            initial_page_count = session1.page_count
        
        # Request same session again
        with app.test_request_context(
            '/about',
            headers={'User-Agent': 'Mozilla/5.0 Chrome/119.0.0.0'},
            environ_base={'REMOTE_ADDR': '127.0.0.1'}
        ):
            from flask import request
            session2 = get_or_create_session('test_session_456', request)
            
            assert session2.id == session1.id
            assert session2.page_count == initial_page_count + 1
    
    def test_marks_returning_visitor(self, app, database):
        """Should mark visitor as returning if has previous sessions."""
        # Create first session
        with app.test_request_context(
            '/',
            environ_base={'REMOTE_ADDR': '192.168.1.1'}
        ):
            from flask import request
            session1 = get_or_create_session('session_first', request)
            assert session1.is_returning is False
        
        # Create second session from same IP
        with app.test_request_context(
            '/',
            environ_base={'REMOTE_ADDR': '192.168.1.1'}
        ):
            from flask import request
            session2 = get_or_create_session('session_second', request)
            assert session2.is_returning is True
    
    def test_updates_last_seen(self, app, database):
        """Should update last_seen timestamp."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            from flask import request
            session = get_or_create_session('test_session_time', request)
            first_seen = session.last_seen
            
            # Small delay to ensure timestamp difference
            import time
            time.sleep(0.1)
            
            # Update session
            session2 = get_or_create_session('test_session_time', request)
            assert session2.last_seen > first_seen
    
    def test_handles_missing_user_agent(self, app, database):
        """Should handle missing User-Agent header."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            from flask import request
            session = get_or_create_session('test_no_ua', request)
            
            assert session.device_type == 'unknown'
            assert session.browser == 'unknown'
            assert session.os == 'unknown'


class TestTrackEvent:
    """Test custom event tracking."""
    
    def test_tracks_custom_event(self, app, database):
        """Should track custom analytics event."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            from flask import request
            session = get_or_create_session('test_event_session', request)
            
            event = track_event(
                session.session_id,
                'button_click',
                'contact_button',
                '/contact',
                'submit_btn',
                {'form_type': 'contact'}
            )
            
            assert event is not None
            assert event.session_id == session.session_id
            assert event.event_type == 'button_click'
            assert event.event_name == 'contact_button'
    
    def test_handles_missing_event_data(self, app, database):
        """Should handle missing event data."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            from flask import request
            session = get_or_create_session('test_event_nodata', request)
            
            event = track_event(session.session_id, 'page_scroll', 'scroll_50')
            
            assert event is not None
            assert event.event_type == 'page_scroll'


class TestGetAnalyticsSummary:
    """Test analytics summary generation."""
    
    def test_returns_summary_dict(self, app, database):
        """Should return dictionary with analytics summary."""
        summary = get_analytics_summary(days=30)
        
        assert isinstance(summary, dict)
        assert 'total_views' in summary
        assert 'unique_sessions' in summary
        assert 'popular_pages' in summary
    
    def test_includes_device_stats(self, app, database):
        """Should include device statistics."""
        summary = get_analytics_summary(days=30)
        
        assert 'device_stats' in summary
        assert isinstance(summary['device_stats'], list)
    
    def test_includes_browser_stats(self, app, database):
        """Should include browser statistics."""
        summary = get_analytics_summary(days=30)
        
        assert 'browser_stats' in summary
        assert isinstance(summary['browser_stats'], list)
    
    def test_respects_days_parameter(self, app, database):
        """Should respect days parameter."""
        # This is a smoke test - actual behavior depends on data
        summary_7 = get_analytics_summary(days=7)
        summary_30 = get_analytics_summary(days=30)
        
        assert isinstance(summary_7, dict)
        assert isinstance(summary_30, dict)


class TestGetDailyTraffic:
    """Test daily traffic retrieval."""
    
    def test_returns_list_of_days(self, app, database):
        """Should return list of daily traffic data."""
        traffic = get_daily_traffic(days=7)
        
        assert isinstance(traffic, list)
    
    def test_includes_date_and_views(self, app, database):
        """Should include date and views in results."""
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            from flask import request
            session = get_or_create_session('test_traffic', request)
            
            # Create a page view
            page_view = PageView(
                session_id=session.session_id,
                path='/',
                device_type='desktop',
                browser='Chrome',
                os='Windows',
                created_at=datetime.now(timezone.utc)
            )
            db.session.add(page_view)
            db.session.commit()
        
        traffic = get_daily_traffic(days=7)
        
        if traffic:
            assert 'date' in traffic[0]
            assert 'views' in traffic[0]
    
    def test_respects_limit_parameter(self, app, database):
        """Should respect days limit parameter."""
        traffic_3 = get_daily_traffic(days=3)
        traffic_30 = get_daily_traffic(days=30)
        
        assert isinstance(traffic_3, list)
        assert isinstance(traffic_30, list)
        # 30-day query should potentially return more days than 3-day
        assert len(traffic_30) >= len(traffic_3)
