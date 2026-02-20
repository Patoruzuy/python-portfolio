"""
Python Developer Portfolio Website
A Flask-based portfolio showcasing Python projects, Raspberry Pi implementations,
technical blog, and e-commerce capabilities.
"""

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_caching import Cache
from datetime import datetime, timezone
from sqlalchemy.exc import SQLAlchemyError
import os
import sys
from slugify import slugify
from config import get_config, DopplerConfig
from models import (
    db, Project, Product, RaspberryPiProject, BlogPost,
    OwnerProfile, SiteConfig, PageView, Newsletter, UserSession, AnalyticsEvent
)
from utils.analytics_utils import parse_user_agent, get_or_create_session
from celery_config import make_celery, celery  # noqa: F401
from scripts.cache_buster import init_cache_buster
from utils.endpoint_url_fallbacks import install_endpoint_url_for_fallback
from utils.csp_manager import init_csp
from utils.rate_limiter import init_limiter, create_rate_limit_error_handler, RATE_LIMITS
from typing import Optional, Dict, Any, Tuple, Union
from flask import Response


def safe_console_log(message: str, fallback: Optional[str] = None) -> None:
    """Print startup/runtime messages without crashing on limited terminals."""
    try:
        print(message)
    except UnicodeEncodeError:
        if fallback:
            print(fallback)
            return
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        safe_message = message.encode(encoding, errors='replace').decode(encoding)
        print(safe_message)

# Initialize Flask app
app = Flask(__name__)

# Load configuration from config.py (supports .env and Doppler)
config_class = get_config()
app.config.from_object(config_class)

# Log configuration source
if DopplerConfig.is_doppler_active():
    doppler_info = DopplerConfig.get_doppler_info()
    safe_console_log(
        f"🔐 Configuration loaded from Doppler: {doppler_info}",
        fallback=f"[INFO] Configuration loaded from Doppler: {doppler_info}"
    )
else:
    safe_console_log(
        "📁 Configuration loaded from .env file",
        fallback="[INFO] Configuration loaded from .env file"
    )

# Initialize DB with App
db.init_app(app)

# Security: CSRF Protection
csrf = CSRFProtect(app)

# Cache Configuration
cache = Cache(app, config={
    'CACHE_TYPE': app.config.get('CACHE_TYPE', 'simple'),
    'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
    'CACHE_REDIS_URL': app.config.get('CACHE_REDIS_URL')
})

# Initialize Celery with Flask app context
make_celery(app)  # Integrate Flask app context with Celery

# Initialize Cache Buster for static assets
cache_buster = init_cache_buster(app)

# Initialize CSP Manager with nonce support
csp = init_csp(app)

# Initialize Rate Limiter with Redis storage (must be before routes)
limiter = init_limiter(app)
rate_limit_handler = create_rate_limit_error_handler(limiter)
app.register_error_handler(429, rate_limit_handler)

safe_console_log(
    "🛡️  Rate limiting enabled with Redis storage",
    fallback="[INFO] Rate limiting enabled"
)

# Security: HTTP Headers (HSTS, etc.)
# CSP is now handled by csp_manager.py
# Disable Talisman in testing mode to avoid HTTPS redirects
if not app.config.get('TESTING'):
    Talisman(app, content_security_policy=None)

# Register admin blueprint
from admin_routes import admin_bp  # noqa: E402
app.register_blueprint(admin_bp)
install_endpoint_url_for_fallback(app)

# Error Handlers


@app.errorhandler(404)
def page_not_found(e: Exception) -> Tuple[str, int]:
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e: Exception) -> Tuple[str, int]:
    # Reusing 404 template for simplicity, tailored message could be added
    return render_template('404.html'), 500


# Initialize Flask-Mail (config loaded from DB in routes)
mail = Mail(app)

# Load email configuration from database or environment


def configure_email_from_db() -> None:
    """Load email settings from SiteConfig or fall back to config.py"""
    with app.app_context():
        try:
            config = SiteConfig.query.first()
            if config:
                # Use database config if available, otherwise fall back to app.config
                app.config['MAIL_SERVER'] = config.mail_server or app.config.get('MAIL_SERVER')
                app.config['MAIL_PORT'] = config.mail_port or app.config.get('MAIL_PORT')
                app.config['MAIL_USE_TLS'] = config.mail_use_tls if config.mail_use_tls is not None else app.config.get('MAIL_USE_TLS')
                app.config['MAIL_USERNAME'] = config.mail_username or app.config.get('MAIL_USERNAME')
                app.config['MAIL_DEFAULT_SENDER'] = config.mail_default_sender or app.config.get('MAIL_DEFAULT_SENDER')
                app.config['MAIL_RECIPIENT'] = config.mail_recipient or app.config.get('MAIL_RECIPIENT')
            # else: app.config already has values from config.py
        except (SQLAlchemyError, RuntimeError) as e:
            # Database not initialized yet or table doesn't exist
            # Fall back to config.py values which are already loaded
            safe_console_log(
                f"⚠️  Could not load email config from database: {e}",
                fallback="[WARNING] Could not load email config from database"
            )
            pass
        
        # Password and CONTACT_EMAIL always from config (env/Doppler) for security
        # These are already set in app.config from config.py
        
        # Reinitialize Flask-Mail with new config
        mail.init_app(app)


# Initialize database tables (skip auto-init during tests)
if app.config.get('TESTING'):
    safe_console_log(
        "[INFO] Testing mode: skipping automatic database initialization"
    )
    configure_email_from_db()
else:
    with app.app_context():
        # IMPORTANT: create_all() only creates missing tables, it does NOT drop existing data
        # However, for extra safety, we check if DB exists before running migrations
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        db_exists = os.path.exists(db_path) if 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI'] else True
        
        if db_exists:
            safe_console_log(
                "📊 Database found - preserving existing data",
                fallback="[INFO] Database found - preserving existing data"
            )
        else:
            safe_console_log(
                "🆕 Creating new database schema",
                fallback="[INFO] Creating new database schema"
            )
        
        db.create_all()  # Safe: only creates missing tables, preserves existing data
        
        # Auto-migrate: Add new columns if they don't exist
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        
        # Migrate RaspberryPiProject table with new resource columns
        if 'raspberry_pi_projects' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('raspberry_pi_projects')]
            new_columns = [
                ('documentation_json', 'TEXT'),
                ('circuit_diagrams_json', 'TEXT'),
                ('parts_list_json', 'TEXT'),
                ('videos_json', 'TEXT')
            ]
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    db.session.execute(text(f"ALTER TABLE raspberry_pi_projects ADD COLUMN {col_name} {col_type}"))
            db.session.commit()
        
        configure_email_from_db()  # Load email config from DB


@app.context_processor
def inject_global_data() -> Dict[str, Any]:
    """Inject owner profile and site config into all templates"""
    try:
        owner = OwnerProfile.query.first()
        config = SiteConfig.query.first()
    except SQLAlchemyError:
        db.session.rollback()
        owner = None
        config = None

    # Create default objects if missing
    if not owner:
        owner = OwnerProfile(
            name="Portfolio Owner",
            title="Developer",
            email="contact@example.com"
        )

    if not config:
        config = SiteConfig(
            site_name="Developer Portfolio",
            blog_enabled=True,
            products_enabled=True
        )

    return dict(
        owner=owner,
        site_config=config
    )


@app.before_request
def track_analytics() -> None:
    """Track page views and sessions for analytics"""
    # Skip tracking for static files and API endpoints
    if request.path.startswith('/static/') or request.path.startswith('/api/analytics'):
        return
    
    # Respect Do Not Track browser setting
    dnt = request.headers.get('DNT') or request.headers.get('dnt')
    if dnt == '1':
        return
    
    # Check if analytics is enabled
    try:
        config = SiteConfig.query.first()
    except SQLAlchemyError:
        db.session.rollback()
        return

    if not config or not config.analytics_enabled:
        return
    
    # Check if user has consented to cookies
    cookie_consent = request.cookies.get('cookie_consent')
    if cookie_consent != 'accepted':
        return
    
    try:
        import uuid
        
        # Get or create session ID
        session_id = request.cookies.get('analytics_session')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Get or create session
        get_or_create_session(session_id, request)
        
        # Parse user agent
        ua_info = parse_user_agent(request.user_agent.string)
        
        # Deduplicate: Check if same session visited same path in last 30 seconds
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        recent_view = PageView.query.filter(
            PageView.session_id == session_id,
            PageView.path == request.path,
            PageView.created_at >= cutoff_time
        ).first()
        
        # Only track if no recent duplicate view
        if not recent_view:
            page_view = PageView(
                path=request.path,
                referrer=request.referrer,
                user_agent=request.user_agent.string[:300] if request.user_agent.string else None,
                ip_address=request.remote_addr,
                session_id=session_id,
                device_type=ua_info['device_type'],
                browser=ua_info['browser'],
                os=ua_info['os']
            )
            db.session.add(page_view)
            db.session.commit()
        
        # Set session cookie if new
        if not request.cookies.get('analytics_session'):
            from flask import make_response
            # Store for after_request
            request.new_analytics_session = session_id
            
    except Exception as e:
        print(f"Analytics tracking error: {e}")
        db.session.rollback()


@app.after_request
def set_analytics_cookie(response: Response) -> Response:
    """Set analytics session cookie if new session was created"""
    if hasattr(request, 'new_analytics_session'):
        response.set_cookie(
            'analytics_session',
            request.new_analytics_session,
            max_age=30*24*60*60,  # 30 days
            httponly=True,
            samesite='Lax'
        )
    return response

# All data now loaded from database models
# Blog posts, products, and Raspberry Pi projects migrated to DB


# All data now loaded from database models
# Blog posts, products, and Raspberry Pi projects migrated to DB

# ========== ROUTES ==========

@app.route('/')
def index() -> str:
    """Homepage with overview and featured projects"""
    # Fetch featured projects from DB
    db_projects = Project.query.filter_by(featured=True).limit(3).all()

    # Process for template
    featured_projects = []
    for p in db_projects:
        featured_projects.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'technologies': [t.strip() for t in p.technologies.split(',')] if p.technologies else [],
            'category': p.category,
            'image': p.image_url,
            'github': p.github_url,
            'demo': p.demo_url
        })

    # Fetch recent blog posts from DB
    recent_posts = BlogPost.query.filter_by(
        published=True).order_by(
        BlogPost.created_at.desc()).limit(3).all()

    return render_template('index.html',
                           featured_projects=featured_projects,
                           recent_posts=recent_posts)


@app.route('/projects')
def projects() -> str:
    """Projects showcase page"""
    db_projects = Project.query.all()

    # Process for template
    processed_projects = []
    for p in db_projects:
        processed_projects.append({
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'technologies': [t.strip() for t in p.technologies.split(',')] if p.technologies else [],
            'category': p.category,
            'image': p.image_url,
            'github': p.github_url,
            'demo': p.demo_url
        })

    return render_template('projects.html', projects=processed_projects)


@app.route('/projects/<int:project_id>')
def project_detail(project_id: int) -> str:
    """Individual project detail page"""
    project = Project.query.get_or_404(project_id)

    # Convert to dict for template
    p_dict = {
        'id': project.id,
        'title': project.title,
        'description': project.description,
        'technologies': [
            t.strip() for t in project.technologies.split(',')] if project.technologies else [],
        'category': project.category,
        'image': project.image_url,
        'github': project.github_url,
        'demo': project.demo_url}

    return render_template('project_detail.html', project=p_dict)


@app.route('/raspberry-pi')
def raspberry_pi() -> str:
    """Raspberry Pi projects showcase"""
    rpi_projects = RaspberryPiProject.query.all()
    return render_template('raspberry_pi.html', projects=rpi_projects)


@app.route('/raspberry-pi/<int:project_id>/resources')
def rpi_resources(project_id: int) -> str:
    """Raspberry Pi project resources page"""
    project = RaspberryPiProject.query.get_or_404(project_id)
    return render_template('rpi_resources.html', project=project)


@app.route('/blog')
def blog() -> str:
    """Blog listing page"""
    posts = BlogPost.query.filter_by(
        published=True).order_by(
        BlogPost.created_at.desc()).all()
    return render_template('blog.html', posts=posts)


@app.route('/blog/<slug>')
def blog_post(slug: str) -> str:
    """Individual blog post page"""
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()

    # Track analytics if enabled
    config = SiteConfig.query.first()
    if config and config.analytics_enabled:
        try:
            # Get session ID from cookie or create new one
            session_id = request.cookies.get('analytics_session')
            if not session_id:
                import uuid
                session_id = str(uuid.uuid4())
            
            # Get or create session
            get_or_create_session(session_id, request)
            
            # Parse user agent for device info
            ua_info = parse_user_agent(request.user_agent.string)
            
            page_view = PageView(
                path=f'/blog/{slug}',
                referrer=request.referrer,
                user_agent=request.user_agent.string,
                ip_address=request.remote_addr,
                session_id=session_id,
                device_type=ua_info['device_type'],
                browser=ua_info['browser'],
                os=ua_info['os']
            )
            db.session.add(page_view)

            # Increment post view count
            post.view_count += 1
            db.session.commit()
        except Exception as e:
            print(f"Analytics error: {e}")
            db.session.rollback()

    return render_template('blog_post.html', post=post)


@app.route('/products')
def products() -> str:
    """E-commerce products page"""
    db_products = Product.query.all()
    return render_template('products.html', products=db_products)


@app.route('/about')
def about() -> str:
    """About page with bio and skills"""
    # about_info is now injected via context processor
    return render_template('about.html')


@app.route('/contact')
def contact() -> str:
    """Contact page"""
    # contact_info is already injected by context_processor
    return render_template('contact.html')


# API endpoints for dynamic filtering
@app.route('/api/projects')
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


@app.route('/api/blog')
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


@app.route('/api/contact', methods=['POST'])
@csrf.exempt  # Temporarily exempt for testing - remove in production if using form-based submission
@limiter.limit(RATE_LIMITS['api_contact'])
def api_contact() -> Tuple[Response, int]:
    """API endpoint for contact form submission with async email processing"""
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
        from tasks.email_tasks import send_contact_email

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


@app.route('/api/newsletter/subscribe', methods=['POST'])
@csrf.exempt  # For AJAX requests
@limiter.limit(RATE_LIMITS['api_newsletter'])
def api_newsletter_subscribe() -> Tuple[Response, int]:
    """API endpoint for newsletter subscription"""
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
        from tasks.email_tasks import send_newsletter_confirmation
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


@app.route('/newsletter/confirm/<token>')
def newsletter_confirm(token: str) -> Response:
    """Confirm newsletter subscription"""
    try:
        subscription = Newsletter.query.filter_by(
            confirmation_token=token).first()

        if not subscription:
            flash('Invalid confirmation link.', 'error')
            return redirect(url_for('blog'))

        if subscription.confirmed:
            flash('Your subscription is already confirmed!', 'info')
            return redirect(url_for('blog'))

        subscription.confirmed = True
        db.session.commit()

        flash(
            '🎉 Subscription confirmed! You will now receive our newsletter.',
            'success')
        return redirect(url_for('blog'))

    except Exception as e:
        print(f"Newsletter confirmation error: {e}")
        flash('Confirmation failed. Please try again.', 'error')
        return redirect(url_for('blog'))


@app.route('/newsletter/unsubscribe/<token>')
def newsletter_unsubscribe(token: str) -> Response:
    """Unsubscribe from newsletter"""
    try:
        subscription = Newsletter.query.filter_by(
            confirmation_token=token).first()

        if not subscription:
            flash('Invalid unsubscribe link.', 'error')
            return redirect(url_for('blog'))

        if not subscription.active:
            flash('You are already unsubscribed.', 'info')
            return redirect(url_for('blog'))

        subscription.active = False
        subscription.unsubscribed_at = datetime.now(timezone.utc)
        db.session.commit()

        flash('You have been unsubscribed from the newsletter.', 'info')
        return redirect(url_for('blog'))

    except Exception as e:
        print(f"Newsletter unsubscribe error: {e}")
        flash('Unsubscribe failed. Please try again.', 'error')
        return redirect(url_for('blog'))


@app.route('/admin/analytics')
def analytics_dashboard() -> str:
    """Analytics dashboard page - shows traffic and user behavior metrics"""
    from utils.analytics_utils import get_analytics_summary, get_daily_traffic
    from sqlalchemy import func
    
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
        BlogPost.published == True
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


@app.route('/api/analytics/event', methods=['POST'])
def track_analytics_event() -> Tuple[Response, int]:
    """API endpoint for tracking custom analytics events from JavaScript"""
    from utils.analytics_utils import track_event
    
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


@app.route('/privacy-policy')
def privacy_policy() -> str:
    """Privacy policy and cookie information"""
    return render_template('privacy_policy.html')


@app.route('/api/cookie-consent', methods=['POST'])
def log_cookie_consent() -> Tuple[Response, int]:
    """Log cookie consent decisions for GDPR compliance audit trail"""
    from models import CookieConsent
    
    try:
        data = request.json
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


@app.route('/my-data')
def my_data_page() -> str:
    """Page for users to view and download their data"""
    return render_template('my_data.html')


@app.route('/api/my-data/download')
def download_my_data() -> Union[Response, Tuple[Response, int]]:
    """Export user's analytics data (GDPR data portability right)"""
    import json
    from io import BytesIO
    from flask import send_file
    
    try:
        session_id = request.cookies.get('analytics_session')
        
        if not session_id:
            return jsonify({'error': 'No session found'}), 404
        
        # Collect user's data
        user_data = {
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
        from models import CookieConsent
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


@app.route('/api/my-data/delete', methods=['POST'])
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


@app.route('/health')
def health() -> Tuple[Response, int]:
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@app.template_filter('format_date')
def format_date(date_string: Union[str, datetime]) -> str:
    """Template filter for date formatting"""
    if isinstance(date_string, datetime):
        return date_string.strftime('%B %d, %Y')
    try:
        date = datetime.strptime(date_string, '%Y-%m-%d')
        return date.strftime('%B %d, %Y')
    except BaseException:
        return str(date_string)


@app.template_filter('slugify')
def slugify_filter(value: str) -> str:
    """Template filter for slug generation"""
    return slugify(value)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=port)
