"""
Public-facing routes blueprint.
Handles: homepage, projects, blog, about, contact, products.
"""
from flask import Blueprint, render_template, request
from models import (
    db, Project, Product, RaspberryPiProject, BlogPost,
    SiteConfig, PageView
)
from utils.analytics_utils import parse_user_agent, get_or_create_session

# Create public blueprint
public_bp = Blueprint('public', __name__)


@public_bp.route('/')
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


@public_bp.route('/projects')
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


@public_bp.route('/projects/<int:project_id>')
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


@public_bp.route('/raspberry-pi')
def raspberry_pi() -> str:
    """Raspberry Pi projects showcase"""
    rpi_projects = RaspberryPiProject.query.all()
    return render_template('raspberry_pi.html', projects=rpi_projects)


@public_bp.route('/raspberry-pi/<int:project_id>/resources')
def rpi_resources(project_id: int) -> str:
    """Raspberry Pi project resources page"""
    project = RaspberryPiProject.query.get_or_404(project_id)
    return render_template('rpi_resources.html', project=project)


@public_bp.route('/blog')
def blog() -> str:
    """Blog listing page"""
    posts = BlogPost.query.filter_by(
        published=True).order_by(
        BlogPost.created_at.desc()).all()
    return render_template('blog.html', posts=posts)


@public_bp.route('/blog/<slug>')
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


@public_bp.route('/products')
def products() -> str:
    """E-commerce products page"""
    db_products = Product.query.all()
    return render_template('products.html', products=db_products)


@public_bp.route('/about')
def about() -> str:
    """About page with bio and skills"""
    # about_info is now injected via context processor
    return render_template('about.html')


@public_bp.route('/contact')
def contact() -> str:
    """Contact page"""
    # contact_info is already injected by context_processor
    return render_template('contact.html')
