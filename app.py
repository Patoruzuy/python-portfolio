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
import os
from dotenv import load_dotenv
from slugify import slugify
from models import (
    db, Project, Product, RaspberryPiProject, BlogPost,
    OwnerProfile, SiteConfig, PageView, Newsletter
)
from celery_config import make_celery, celery  # noqa: F401
from scripts.cache_buster import init_cache_buster
from csp_manager import init_csp

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv(
    'SECRET_KEY', 'dev-secret-key-change-in-production')

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB with App
db.init_app(app)

# Security: CSRF Protection
csrf = CSRFProtect(app)

# Cache Configuration
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Celery Configuration (async tasks)
app.config['CELERY_BROKER_URL'] = os.getenv(
    'CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.getenv(
    'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Site Configuration
app.config['SITE_URL'] = os.getenv('SITE_URL', 'http://localhost:5000')

# Initialize Celery with Flask app context
make_celery(app)  # Integrate Flask app context with Celery

# Initialize Cache Buster for static assets
cache_buster = init_cache_buster(app)

# Initialize CSP Manager with nonce support
csp = init_csp(app)

# Security: HTTP Headers (HSTS, etc.)
# CSP is now handled by csp_manager.py
# Disable Talisman in testing mode to avoid HTTPS redirects
if not os.getenv('FLASK_TESTING'):
    Talisman(app, content_security_policy=None)

# Register admin blueprint
from admin_routes import admin_bp  # noqa: E402
app.register_blueprint(admin_bp)

# Error Handlers


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    # Reusing 404 template for simplicity, tailored message could be added
    return render_template('404.html'), 500


# Initialize Flask-Mail (config loaded from DB in routes)
mail = Mail(app)

# Load email configuration from database or environment


def configure_email_from_db():
    """Load email settings from SiteConfig or fall back to .env"""
    with app.app_context():
        config = SiteConfig.query.first()
        if config:
            app.config['MAIL_SERVER'] = config.mail_server or os.getenv(
                'MAIL_SERVER', 'smtp.gmail.com')
            app.config['MAIL_PORT'] = config.mail_port or int(
                os.getenv('MAIL_PORT', 587))
            app.config['MAIL_USE_TLS'] = config.mail_use_tls if config.mail_use_tls is not None else True
            app.config['MAIL_USERNAME'] = config.mail_username or os.getenv(
                'MAIL_USERNAME')
            app.config['MAIL_DEFAULT_SENDER'] = config.mail_default_sender or os.getenv(
                'MAIL_DEFAULT_SENDER')
            app.config['MAIL_RECIPIENT'] = config.mail_recipient or os.getenv(
                'MAIL_RECIPIENT')
        else:
            # Fallback to environment variables
            app.config['MAIL_SERVER'] = os.getenv(
                'MAIL_SERVER', 'smtp.gmail.com')
            app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
            app.config['MAIL_USE_TLS'] = os.getenv(
                'MAIL_USE_TLS', 'True') == 'True'
            app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
            app.config['MAIL_DEFAULT_SENDER'] = os.getenv(
                'MAIL_DEFAULT_SENDER')
            app.config['MAIL_RECIPIENT'] = os.getenv('MAIL_RECIPIENT')

        # Password always from .env for security
        app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')


# Initialize database tables
with app.app_context():
    db.create_all()
    configure_email_from_db()  # Load email config from DB


@app.context_processor
def inject_global_data():
    """Inject owner profile and site config into all templates"""
    owner = OwnerProfile.query.first()
    config = SiteConfig.query.first()

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

# All data now loaded from database models
# Blog posts, products, and Raspberry Pi projects migrated to DB


# All data now loaded from database models
# Blog posts, products, and Raspberry Pi projects migrated to DB

# ========== ROUTES ==========

@app.route('/')
def index():
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
def projects():
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
def project_detail(project_id):
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
def raspberry_pi():
    """Raspberry Pi projects showcase"""
    rpi_projects = RaspberryPiProject.query.all()
    return render_template('raspberry_pi.html', projects=rpi_projects)


@app.route('/blog')
def blog():
    """Blog listing page"""
    posts = BlogPost.query.filter_by(
        published=True).order_by(
        BlogPost.created_at.desc()).all()
    return render_template('blog.html', posts=posts)


@app.route('/blog/<slug>')
def blog_post(slug):
    """Individual blog post page"""
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()

    # Track analytics if enabled
    config = SiteConfig.query.first()
    if config and config.analytics_enabled:
        try:
            page_view = PageView(
                path=f'/blog/{slug}',
                referrer=request.referrer,
                user_agent=request.user_agent.string,
                ip_address=request.remote_addr
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
def products():
    """E-commerce products page"""
    db_products = Product.query.all()
    return render_template('products.html', products=db_products)


@app.route('/about')
def about():
    """About page with bio and skills"""
    # about_info is now injected via context processor
    return render_template('about.html')


@app.route('/contact')
def contact():
    """Contact page"""
    # contact_info is already injected by context_processor
    return render_template('contact.html')


# API endpoints for dynamic filtering
@app.route('/api/projects')
def api_projects():
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
def api_blog():
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
def api_contact():
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
def api_newsletter_subscribe():
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
def newsletter_confirm(token):
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
def newsletter_unsubscribe(token):
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


@app.route('/health')
def health():
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
def format_date(date_string):
    """Template filter for date formatting"""
    if isinstance(date_string, datetime):
        return date_string.strftime('%B %d, %Y')
    try:
        date = datetime.strptime(date_string, '%Y-%m-%d')
        return date.strftime('%B %d, %Y')
    except BaseException:
        return str(date_string)


@app.template_filter('slugify')
def slugify_filter(value):
    """Template filter for slug generation"""
    return slugify(value)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
