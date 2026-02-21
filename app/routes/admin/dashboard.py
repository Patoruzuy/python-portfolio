"""
Admin dashboard and analytics routes.
"""
from flask import Blueprint, render_template, request
from app.models import db, Project, Product, RaspberryPiProject, BlogPost, PageView, Newsletter, AnalyticsEvent
from app.routes.admin.utils import login_required
from sqlalchemy import func, select, case, and_

# Create admin dashboard blueprint
admin_dashboard_bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')


@admin_dashboard_bp.route('/')
@admin_dashboard_bp.route('/dashboard')
@login_required
def dashboard() -> str:
    """Admin dashboard with content statistics (optimized with subqueries)."""
    # Use scalar subqueries - executes as single query with subselects
    stmt = select(
        select(func.count(Project.id)).scalar_subquery().label('projects'),
        select(func.count(Product.id)).scalar_subquery().label('products'),
        select(func.count(RaspberryPiProject.id)).scalar_subquery().label('raspberry_pi'),
        select(func.count(BlogPost.id)).scalar_subquery().label('blog_posts'),
        select(func.count(PageView.id)).scalar_subquery().label('page_views'),
        select(func.count(Newsletter.id)).where(Newsletter.active == True).scalar_subquery().label('newsletter_subscribers')  # noqa: E712
    )
    
    result = db.session.execute(stmt).first()
    
    # Build stats dictionary from result
    stats = {
        'projects': result.projects if result else 0,
        'products': result.products if result else 0,
        'raspberry_pi': result.raspberry_pi if result else 0,
        'blog_posts': result.blog_posts if result else 0,
        'page_views': result.page_views if result else 0,
        'newsletter_subscribers': result.newsletter_subscribers if result else 0
    }
    
    return render_template('admin/dashboard.html', stats=stats)


@admin_dashboard_bp.route('/analytics')
@login_required
def analytics() -> str:
    """View page analytics and statistics."""
    from app.utils.analytics_utils import get_analytics_summary, get_daily_traffic

    # Get analytics period from query param (default 30 days)
    days = request.args.get('days', 30, type=int)
    
    # Get analytics summary
    summary = get_analytics_summary(days)
    
    # Get daily traffic for chart
    daily_traffic = get_daily_traffic(days)
    
    # Get newsletter stats with single query using case statements
    newsletter_stats = db.session.query(
        func.count(Newsletter.id).label('total'),
        func.coalesce(func.sum(case((Newsletter.active == True, 1), else_=0)), 0).label('active'),  # noqa: E712
        func.coalesce(  # noqa: E712
            func.sum(
                case((and_(Newsletter.active.is_(True), Newsletter.confirmed.is_(True)), 1), else_=0)
            ),
            0,
        ).label('confirmed_active'),
        func.coalesce(func.sum(case((Newsletter.active == False, 1), else_=0)), 0).label('unsubscribed')  # noqa: E712
    ).first()

    active_subscribers = int(newsletter_stats.active) if newsletter_stats else 0
    total_subscribers = int(newsletter_stats.confirmed_active) if newsletter_stats else 0
    unconfirmed = max(active_subscribers - total_subscribers, 0)
    unsubscribed = int(newsletter_stats.unsubscribed or 0) if newsletter_stats else 0
    
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
