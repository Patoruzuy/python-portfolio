"""
Analytics utility functions for tracking and parsing user data.
"""
from user_agents import parse
from datetime import datetime, timezone
from models import UserSession, PageView, AnalyticsEvent, db


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract device, browser, and OS info.
    
    Args:
        user_agent_string (str): The user agent string from request headers
        
    Returns:
        dict: Dictionary with device_type, browser, and os information
    """
    if not user_agent_string:
        return {
            'device_type': 'unknown',
            'browser': 'unknown',
            'os': 'unknown'
        }
    
    ua = parse(user_agent_string)
    
    # Determine device type
    if ua.is_mobile:
        device_type = 'mobile'
    elif ua.is_tablet:
        device_type = 'tablet'
    elif ua.is_pc:
        device_type = 'desktop'
    else:
        device_type = 'other'
    
    # Get browser name and version
    browser = f"{ua.browser.family}"
    if ua.browser.version_string:
        browser += f" {ua.browser.version_string}"
    
    # Get OS name and version
    os = f"{ua.os.family}"
    if ua.os.version_string:
        os += f" {ua.os.version_string}"
    
    return {
        'device_type': device_type,
        'browser': browser[:50],  # Limit to column size
        'os': os[:50]  # Limit to column size
    }


def get_or_create_session(session_id, request):
    """
    Get existing session or create a new one.
    
    Args:
        session_id (str): Unique session identifier
        request: Flask request object
        
    Returns:
        UserSession: The session object
    """
    session = UserSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        # Parse user agent
        ua_info = parse_user_agent(request.headers.get('User-Agent', ''))
        
        # Check if returning visitor (has previous sessions from same IP)
        is_returning = UserSession.query.filter_by(
            ip_address=request.remote_addr
        ).first() is not None
        
        session = UserSession(
            session_id=session_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:300],
            device_type=ua_info['device_type'],
            browser=ua_info['browser'],
            os=ua_info['os'],
            is_returning=is_returning,
            page_count=0
        )
        db.session.add(session)
    
    # Update last seen and page count
    session.last_seen = datetime.now(timezone.utc)
    session.page_count += 1
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error updating session: {e}")
    
    return session


def track_event(session_id, event_type, event_name, page_path=None, element_id=None, metadata=None):
    """
    Track a custom analytics event.
    
    Args:
        session_id (str): Session identifier
        event_type (str): Type of event (click, form_submit, download, etc.)
        event_name (str): Name of the event
        page_path (str, optional): Page where event occurred
        element_id (str, optional): DOM element ID
        metadata (dict, optional): Additional event data
        
    Returns:
        AnalyticsEvent: The created event object
    """
    event = AnalyticsEvent(
        session_id=session_id,
        event_type=event_type,
        event_name=event_name,
        page_path=page_path,
        element_id=element_id,
        event_data=metadata  # Store in event_data field
    )
    
    db.session.add(event)
    
    try:
        db.session.commit()
        return event
    except Exception as e:
        db.session.rollback()
        print(f"Error tracking event: {e}")
        return None


def get_analytics_summary(days=30):
    """
    Get analytics summary for the dashboard.
    
    Args:
        days (int): Number of days to analyze (default: 30)
        
    Returns:
        dict: Analytics summary with various metrics
    """
    from datetime import timedelta
    from sqlalchemy import func, distinct
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Total page views
    total_views = PageView.query.filter(PageView.created_at >= cutoff_date).count()
    
    # Unique sessions
    unique_sessions = db.session.query(
        func.count(distinct(PageView.session_id))
    ).filter(PageView.created_at >= cutoff_date).scalar()
    
    # Most viewed pages
    popular_pages = db.session.query(
        PageView.path,
        func.count(PageView.id).label('views')
    ).filter(
        PageView.created_at >= cutoff_date
    ).group_by(PageView.path).order_by(func.count(PageView.id).desc()).limit(10).all()
    
    # Device breakdown
    device_stats = db.session.query(
        PageView.device_type,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.created_at >= cutoff_date,
        PageView.device_type.isnot(None)
    ).group_by(PageView.device_type).all()
    
    # Browser breakdown
    browser_stats = db.session.query(
        PageView.browser,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.created_at >= cutoff_date,
        PageView.browser.isnot(None)
    ).group_by(PageView.browser).order_by(func.count(PageView.id).desc()).limit(10).all()
    
    # Traffic sources (referrers)
    referrer_stats = db.session.query(
        PageView.referrer,
        func.count(PageView.id).label('count')
    ).filter(
        PageView.created_at >= cutoff_date,
        PageView.referrer.isnot(None),
        PageView.referrer != ''
    ).group_by(PageView.referrer).order_by(func.count(PageView.id).desc()).limit(10).all()
    
    # New vs returning visitors
    new_visitors = UserSession.query.filter(
        UserSession.first_seen >= cutoff_date,
        UserSession.is_returning == False
    ).count()
    
    returning_visitors = UserSession.query.filter(
        UserSession.first_seen >= cutoff_date,
        UserSession.is_returning == True
    ).count()
    
    # Average pages per session
    avg_pages = db.session.query(
        func.avg(UserSession.page_count)
    ).filter(UserSession.first_seen >= cutoff_date).scalar() or 0
    
    return {
        'total_views': total_views,
        'unique_sessions': unique_sessions or 0,
        'popular_pages': [{'path': p[0], 'views': p[1]} for p in popular_pages],
        'device_stats': [{'device': d[0], 'count': d[1]} for d in device_stats],
        'browser_stats': [{'browser': b[0], 'count': b[1]} for b in browser_stats],
        'referrer_stats': [{'referrer': r[0], 'count': r[1]} for r in referrer_stats],
        'new_visitors': new_visitors,
        'returning_visitors': returning_visitors,
        'avg_pages_per_session': round(avg_pages, 2)
    }


def get_daily_traffic(days=30):
    """
    Get daily traffic data for charting.
    
    Args:
        days (int): Number of days to retrieve
        
    Returns:
        list: List of dicts with date and view count
    """
    from datetime import timedelta
    from sqlalchemy import func
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Use func.date() for SQLite compatibility (returns string)
    date_col = func.date(PageView.created_at).label('date')
    
    daily_data = db.session.query(
        date_col,
        func.count(PageView.id).label('views')
    ).filter(
        PageView.created_at >= cutoff_date
    ).group_by(date_col).order_by(date_col).all()
    
    return [{'date': d[0], 'views': d[1]} for d in daily_data]
