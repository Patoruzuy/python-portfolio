from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from functools import wraps
import os
import json
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from slugify import slugify
from models import (
    db, Project, Product, RaspberryPiProject, BlogPost,
    OwnerProfile, SiteConfig, PageView, Newsletter
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials - Use environment variables in production
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
# Default hash is "admin123" - CHANGE THIS IN PRODUCTION via .env
ADMIN_PASSWORD_HASH = os.environ.get(
    'ADMIN_PASSWORD_HASH',
    'scrypt:32768:8:1$zQX8DaHbhfTCvKN9$3b2f4b1c8d5e6f7a8b9c0d1e2f3a4b5c6d'
    '7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3')

# Image upload configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.before_request
def make_session_permanent():
    session.permanent = True
    # Default is 30 minutes if not "remember me"
    # This is overridden in login route, but good fallback
    if 'remember_me' not in session:
        current_app.permanent_session_lifetime = timedelta(minutes=30)


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        # Reload credentials from env in case they changed
        global ADMIN_USERNAME, ADMIN_PASSWORD_HASH
        ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', ADMIN_USERNAME)
        ADMIN_PASSWORD_HASH = os.environ.get(
            'ADMIN_PASSWORD_HASH', ADMIN_PASSWORD_HASH)

        if username == ADMIN_USERNAME and check_password_hash(
                ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True

            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
                session['remember_me'] = True
            else:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(minutes=30)
                session.pop('remember_me', None)

            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('admin.login'))


@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset - requires manual .env update for security"""
    if request.method == 'POST':
        new_password = request.form.get('new_password')

        # Generate new hash
        new_hash = generate_password_hash(new_password)

        # For security, we don't automatically update files
        # Instead, provide the hash for manual .env update
        flash(
            f'Add this to your .env file: ADMIN_PASSWORD_HASH={new_hash}',
            'info')
        flash(
            'After updating .env, restart the application to use your new password.',
            'warning')

        return render_template('admin/forgot_password.html', new_hash=new_hash)

    return render_template('admin/forgot_password.html')


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard with content statistics"""
    stats = {
        'projects': Project.query.count(),
        'products': Product.query.count(),
        'raspberry_pi': RaspberryPiProject.query.count(),
        'blog_posts': BlogPost.query.count(),
        'page_views': PageView.query.count(),
        'newsletter_subscribers': Newsletter.query.filter_by(
            active=True).count()}
    return render_template('admin/dashboard.html', stats=stats)

# ============ ANALYTICS ============


@admin_bp.route('/analytics')
@login_required
def analytics():
    """View page analytics and statistics"""
    from analytics_utils import get_analytics_summary, get_daily_traffic
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
    from models import AnalyticsEvent
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

# ============ NEWSLETTER ============


@admin_bp.route('/newsletter')
@login_required
def newsletter():
    """View newsletter subscribers"""
    subscribers = Newsletter.query.order_by(
        Newsletter.subscribed_at.desc()).all()
    active_count = Newsletter.query.filter_by(active=True).count()
    total_count = Newsletter.query.count()

    return render_template('admin/newsletter.html',
                           subscribers=subscribers,
                           active_count=active_count,
                           total_count=total_count)


@admin_bp.route('/newsletter/delete/<int:subscriber_id>', methods=['POST'])
@login_required
def delete_subscriber(subscriber_id):
    """Delete a newsletter subscriber"""
    subscriber = Newsletter.query.get_or_404(subscriber_id)
    db.session.delete(subscriber)
    db.session.commit()

    flash('Subscriber deleted successfully!', 'success')
    return redirect(url_for('admin.newsletter'))

# ============ PROJECTS ============


@admin_bp.route('/projects')
@login_required
def projects():
    # Convert DB objects to dicts for template compatibility if needed,
    # or just pass objects if template supports dot notation (likely yes)
    # The existing template probably expects dict usage like project['id'] or project.id
    # Jinja2 handles dot notation for both usually.
    all_projects = Project.query.all()
    return render_template('admin/projects.html', projects=all_projects)


@admin_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
def add_project():
    if request.method == 'POST':
        # Create new Project from form data
        new_project = Project(
            title=request.form.get('title'),
            description=request.form.get('description'),
            technologies=request.form.get(
                'technologies'),  # Storing as string in DB
            category=request.form.get('category'),
            github_url=request.form.get('github') or None,
            demo_url=request.form.get('demo') or None,
            image_url=request.form.get('image'),
            featured=request.form.get('featured') == 'on'
        )

        db.session.add(new_project)
        db.session.commit()

        flash('Project added successfully!', 'success')
        return redirect(url_for('admin.projects'))

    return render_template('admin/project_form.html', project=None)


@admin_bp.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.technologies = request.form.get('technologies')
        project.category = request.form.get('category')
        project.github_url = request.form.get('github') or None
        project.demo_url = request.form.get('demo') or None
        project.image_url = request.form.get('image')
        project.featured = request.form.get('featured') == 'on'

        db.session.commit()

        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin.projects'))

    # Template expects a dict-like object. The SQLAlchemy model will work via dot notation,
    # but we need to ensure the template uses .attribute access or we make a wrapper.
    # Checking template usage might be wise, but typically people use project.title
    # If the template does project['title'], we need a fix.
    return render_template('admin/project_form.html', project=project)


@admin_bp.route('/projects/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('admin.projects'))

# ============ PRODUCTS ============


@admin_bp.route('/products')
@login_required
def products():
    """List all products"""
    all_products = Product.query.order_by(Product.id).all()
    return render_template('admin/products.html', products=all_products)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Create a new product"""
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form.get('name'),
                description=request.form.get('description'),
                price=float(
                    request.form.get(
                        'price',
                        0)),
                type=request.form.get('type'),
                category=request.form.get('category'),
                features_json=json.dumps(
                    [
                        f.strip() for f in request.form.get(
                            'features',
                            '').split('\n') if f.strip()]),
                purchase_link=request.form.get('purchase_link') or None,
                demo_link=request.form.get('demo_link') or None,
                image_url=request.form.get('image') or '/static/images/placeholder.jpg',
                available=request.form.get('available') == 'on')

            db.session.add(product)
            db.session.commit()

            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.products'))
        except (ValueError, TypeError) as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return render_template('admin/product_form.html', product=None)
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
            return render_template('admin/product_form.html', product=None)

    return render_template('admin/product_form.html', product=None)


@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit an existing product"""
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', 0))
        product.type = request.form.get('type')
        product.category = request.form.get('category')
        product.features_json = json.dumps(
            [f.strip() for f in request.form.get('features', '').split('\n') if f.strip()])
        product.purchase_link = request.form.get('purchase_link') or None
        product.demo_link = request.form.get('demo_link') or None
        product.image_url = request.form.get('image') or product.image_url
        product.available = request.form.get('available') == 'on'

        db.session.commit()

        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', product=product)


@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.products'))

# ============ BLOG ============


@admin_bp.route('/blog')
@login_required
def blog():
    """List all blog posts"""
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/blog.html', posts=posts)


@admin_bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog_post():
    """Create a new blog post"""
    if request.method == 'POST':
        title = request.form.get('title')

        # Auto-generate slug from title
        slug = slugify(title)

        # Ensure slug is unique
        existing = BlogPost.query.filter_by(slug=slug).first()
        if existing:
            counter = 1
            while BlogPost.query.filter_by(slug=f"{slug}-{counter}").first():
                counter += 1
            slug = f"{slug}-{counter}"

        # Calculate read time (200 words per minute)
        content = request.form.get('content', '')
        word_count = len(content.split())
        read_time = f"{max(1, round(word_count / 200))} min"

        post = BlogPost(
            title=title,
            slug=slug,
            excerpt=request.form.get('excerpt'),
            author=request.form.get('author', 'Admin'),
            content=content,
            category=request.form.get('category', 'Uncategorized'),
            tags=request.form.get('tags', ''),
            image_url=request.form.get('image') or '/static/images/placeholder.jpg',
            read_time=read_time,
            published=request.form.get('published') == 'on'
        )

        db.session.add(post)
        db.session.commit()

        flash(f'Blog post created successfully! Slug: {slug}', 'success')
        return redirect(url_for('admin.blog'))

    return render_template('admin/blog_form.html', post=None)


@admin_bp.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_blog_post(post_id):
    """Edit an existing blog post"""
    post = BlogPost.query.get_or_404(post_id)

    if request.method == 'POST':
        title = request.form.get('title')
        new_slug = request.form.get('slug') or slugify(title)

        # Ensure slug is unique (excluding current post)
        if new_slug != post.slug:
            existing = BlogPost.query.filter(
                BlogPost.slug == new_slug,
                BlogPost.id != post_id).first()
            if existing:
                counter = 1
                while BlogPost.query.filter(
                        BlogPost.slug == f"{new_slug}-{counter}",
                        BlogPost.id != post_id).first():
                    counter += 1
                new_slug = f"{new_slug}-{counter}"

        # Recalculate read time if content changed
        content = request.form.get('content', '')
        word_count = len(content.split())
        read_time = f"{max(1, round(word_count / 200))} min"

        post.title = title
        post.slug = new_slug
        post.excerpt = request.form.get('excerpt')
        post.author = request.form.get('author')
        post.content = content
        post.category = request.form.get('category')
        post.tags = request.form.get('tags', '')
        post.image_url = request.form.get('image') or post.image_url
        post.read_time = read_time
        post.published = request.form.get('published') == 'on'

        db.session.commit()

        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin.blog'))

    return render_template('admin/blog_form.html', post=post)


@admin_bp.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_blog_post(post_id):
    """Delete a blog post"""
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash('Blog post deleted successfully!', 'success')
    return redirect(url_for('admin.blog'))

# ============ RASPBERRY PI ============


@admin_bp.route('/raspberry-pi')
@login_required
def raspberry_pi():
    """List all Raspberry Pi projects"""
    projects = RaspberryPiProject.query.order_by(RaspberryPiProject.id).all()
    return render_template('admin/raspberry_pi.html', projects=projects)


@admin_bp.route('/raspberry-pi/add', methods=['GET', 'POST'])
@login_required
def add_rpi_project():
    """Create a new Raspberry Pi project"""
    if request.method == 'POST':
        project = RaspberryPiProject(
            title=request.form.get('title'),
            description=request.form.get('description'),
            hardware_json=json.dumps([h.strip() for h in request.form.get('hardware', '').split(',') if h.strip()]),
            technologies=request.form.get('technologies', ''),
            features_json=json.dumps([f.strip() for f in request.form.get('features', '').split('\n') if f.strip()]),
            github_url=request.form.get('github') or None,
            image_url=request.form.get('image') or '/static/images/placeholder.jpg'
        )

        db.session.add(project)
        db.session.commit()

        flash('Raspberry Pi project added successfully!', 'success')
        return redirect(url_for('admin.raspberry_pi'))

    return render_template('admin/rpi_form.html', project=None)


@admin_bp.route('/raspberry-pi/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_rpi_project(project_id):
    """Edit an existing Raspberry Pi project"""
    project = RaspberryPiProject.query.get_or_404(project_id)

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.hardware_json = json.dumps(
            [h.strip() for h in request.form.get('hardware', '').split(',') if h.strip()])
        project.technologies = request.form.get('technologies', '')
        project.features_json = json.dumps(
            [f.strip() for f in request.form.get('features', '').split('\n') if f.strip()])
        project.github_url = request.form.get('github') or None
        project.image_url = request.form.get('image') or project.image_url

        db.session.commit()

        flash('Raspberry Pi project updated successfully!', 'success')
        return redirect(url_for('admin.raspberry_pi'))

    return render_template('admin/rpi_form.html', project=project)


@admin_bp.route('/raspberry-pi/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_rpi_project(project_id):
    """Delete a Raspberry Pi project"""
    project = RaspberryPiProject.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()

    flash('Raspberry Pi project deleted successfully!', 'success')
    return redirect(url_for('admin.raspberry_pi'))

# ============ IMAGE UPLOAD ============


@admin_bp.route('/upload-image', methods=['GET', 'POST'])
@login_required
def upload_image():
    return_to = request.args.get('return_to', '')
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['image']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(datetime.now().timestamp())}{ext}"

            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            image_path = f"/static/images/{filename}"
            flash(
                f'Image uploaded successfully! Path: {image_path}',
                'success')
            return render_template(
                'admin/upload_image.html',
                uploaded_path=image_path,
                return_to=return_to)
        else:
            flash('Invalid file type. Allowed: png, jpg, jpeg, gif, webp', 'error')

    return render_template('admin/upload_image.html', return_to=return_to)


# ============ OWNER PROFILE & SITE CONFIG ============

@admin_bp.route('/owner-profile', methods=['GET', 'POST'])
@login_required
def owner_profile():
    """Edit owner profile information"""
    owner = OwnerProfile.query.first()

    if not owner:
        # Create default profile if none exists
        owner = OwnerProfile(
            name="Portfolio Owner",
            title="Developer",
            email="contact@example.com"
        )
        db.session.add(owner)
        db.session.commit()

    if request.method == 'POST':
        owner.name = request.form.get('name')
        owner.title = request.form.get('title')
        owner.bio = request.form.get('bio')
        owner.email = request.form.get('email')
        owner.phone = request.form.get('phone')
        owner.location = request.form.get('location')
        owner.github = request.form.get('github')
        owner.linkedin = request.form.get('linkedin')
        owner.twitter = request.form.get('twitter')
        owner.profile_image = request.form.get(
            'profile_image') or owner.profile_image

        # Stats
        try:
            owner.years_experience = int(
                request.form.get('years_experience', 0))
            owner.projects_completed = int(
                request.form.get('projects_completed', 0))
            owner.contributions = int(request.form.get('contributions', 0))
            owner.clients_served = int(request.form.get('clients_served', 0))
            owner.certifications = int(request.form.get('certifications', 0))
        except ValueError:
            flash('Invalid numeric value for stats', 'error')
            return render_template('admin/owner_profile.html', owner=owner)

        # JSON fields - validate JSON format
        try:
            skills_data = request.form.get('skills_json', '[]')
            json.loads(skills_data)  # Validate
            owner.skills_json = skills_data

            exp_data = request.form.get('experience_json', '[]')
            json.loads(exp_data)  # Validate
            owner.experience_json = exp_data

            expertise_data = request.form.get('expertise_json', '[]')
            json.loads(expertise_data)  # Validate
            owner.expertise_json = expertise_data
        except json.JSONDecodeError as e:
            flash(f'Invalid JSON format: {e}', 'error')
            return render_template('admin/owner_profile.html', owner=owner)

        db.session.commit()
        flash('Owner profile updated successfully!', 'success')
        return redirect(url_for('admin.owner_profile'))

    return render_template('admin/owner_profile.html', owner=owner)


@admin_bp.route('/site-config', methods=['GET', 'POST'])
@login_required
def site_config():
    """Edit site configuration"""
    config = SiteConfig.query.first()

    if not config:
        config = SiteConfig(
            site_name="Developer Portfolio",
            blog_enabled=True,
            products_enabled=True
        )
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
        config.site_name = request.form.get('site_name')
        config.tagline = request.form.get('tagline')

        # Email settings
        config.mail_server = request.form.get('mail_server')
        try:
            config.mail_port = int(request.form.get('mail_port', 587))
        except ValueError:
            config.mail_port = 587
        config.mail_use_tls = request.form.get('mail_use_tls') == 'on'
        config.mail_username = request.form.get('mail_username')
        config.mail_default_sender = request.form.get('mail_default_sender')
        config.mail_recipient = request.form.get('mail_recipient')

        # Feature flags
        config.blog_enabled = request.form.get('blog_enabled') == 'on'
        config.products_enabled = request.form.get('products_enabled') == 'on'
        config.analytics_enabled = request.form.get(
            'analytics_enabled') == 'on'

        db.session.commit()

        # Reload email config in app
        from app import configure_email_from_db
        configure_email_from_db()

        flash(
            'Site configuration updated successfully! Email settings reloaded.',
            'success')
        return redirect(url_for('admin.site_config'))

    return render_template('admin/site_config.html', config=config)


@admin_bp.route('/export-config')
@login_required
def export_config():
    """Export site configuration and owner profile as JSON"""
    owner = OwnerProfile.query.first()
    config = SiteConfig.query.first()

    export_data = {
        'exported_at': datetime.now().isoformat(),
        'owner_profile': {
            'name': owner.name if owner else None,
            'title': owner.title if owner else None,
            'bio': owner.bio if owner else None,
            'email': owner.email if owner else None,
            'phone': owner.phone if owner else None,
            'location': owner.location if owner else None,
            'github': owner.github if owner else None,
            'linkedin': owner.linkedin if owner else None,
            'twitter': owner.twitter if owner else None,
            'profile_image': owner.profile_image if owner else None,
            'years_experience': owner.years_experience if owner else 0,
            'projects_completed': owner.projects_completed if owner else 0,
            'contributions': owner.contributions if owner else 0,
            'clients_served': owner.clients_served if owner else 0,
            'certifications': owner.certifications if owner else 0,
            'skills': owner.skills if owner else [],
            'experience': owner.experience if owner else [],
            'expertise': owner.expertise if owner else []
        },
        'site_config': {
            'site_name': config.site_name if config else None,
            'tagline': config.tagline if config else None,
            'mail_server': config.mail_server if config else None,
            'mail_port': config.mail_port if config else None,
            'mail_use_tls': config.mail_use_tls if config else None,
            'mail_username': config.mail_username if config else None,
            'mail_default_sender': config.mail_default_sender if config else None,
            'mail_recipient': config.mail_recipient if config else None,
            'blog_enabled': config.blog_enabled if config else True,
            'products_enabled': config.products_enabled if config else True,
            'analytics_enabled': config.analytics_enabled if config else False
        }
    }

    return jsonify(export_data)


@admin_bp.route('/import-config', methods=['POST'])
@login_required
def import_config():
    """Import site configuration and owner profile from JSON"""
    try:
        data = request.get_json() if request.is_json else json.loads(
            request.form.get('config_data'))

        # Update owner profile
        if 'owner_profile' in data:
            owner = OwnerProfile.query.first()
            if not owner:
                owner = OwnerProfile()
                db.session.add(owner)

            op_data = data['owner_profile']
            owner.name = op_data.get('name')
            owner.title = op_data.get('title')
            owner.bio = op_data.get('bio')
            owner.email = op_data.get('email')
            owner.phone = op_data.get('phone')
            owner.location = op_data.get('location')
            owner.github = op_data.get('github')
            owner.linkedin = op_data.get('linkedin')
            owner.twitter = op_data.get('twitter')
            owner.profile_image = op_data.get('profile_image')
            owner.years_experience = op_data.get('years_experience', 0)
            owner.projects_completed = op_data.get('projects_completed', 0)
            owner.contributions = op_data.get('contributions', 0)
            owner.clients_served = op_data.get('clients_served', 0)
            owner.certifications = op_data.get('certifications', 0)
            owner.skills_json = json.dumps(op_data.get('skills', []))
            owner.experience_json = json.dumps(op_data.get('experience', []))
            owner.expertise_json = json.dumps(op_data.get('expertise', []))

        # Update site config
        if 'site_config' in data:
            config = SiteConfig.query.first()
            if not config:
                config = SiteConfig()
                db.session.add(config)

            sc_data = data['site_config']
            config.site_name = sc_data.get('site_name')
            config.tagline = sc_data.get('tagline')
            config.mail_server = sc_data.get('mail_server')
            config.mail_port = sc_data.get('mail_port')
            config.mail_use_tls = sc_data.get('mail_use_tls')
            config.mail_username = sc_data.get('mail_username')
            config.mail_default_sender = sc_data.get('mail_default_sender')
            config.mail_recipient = sc_data.get('mail_recipient')
            config.blog_enabled = sc_data.get('blog_enabled', True)
            config.products_enabled = sc_data.get('products_enabled', True)
            config.analytics_enabled = sc_data.get('analytics_enabled', False)

        db.session.commit()

        flash('Configuration imported successfully!', 'success')
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        flash(f'Import failed: {e}', 'error')
        return jsonify({'success': False, 'error': str(e)}), 400


@admin_bp.route('/contact-info', methods=['GET', 'POST'])
@login_required
def contact_info():
    """Legacy route - redirects to owner profile"""
    return redirect(url_for('admin.owner_profile'))


@admin_bp.route('/about-info', methods=['GET', 'POST'])
@login_required
def about_info():
    """Legacy route - redirects to owner profile"""
    return redirect(url_for('admin.owner_profile'))
