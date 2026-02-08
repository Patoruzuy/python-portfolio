"""
Python Developer Portfolio Website
A Flask-based portfolio showcasing Python projects, Raspberry Pi implementations,
technical blog, and e-commerce capabilities.
"""

from flask import Flask, render_template, jsonify, request
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from datetime import datetime
import json
import os
import markdown
import re
import bleach
from dotenv import load_dotenv
from markupsafe import Markup
from models import db, Project, About, Contact

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB with App
db.init_app(app)

# Security: CSRF Protection
csrf = CSRFProtect(app)

# Security: HTTP Headers (HSTS, etc.)
# Note: content_security_policy is set to None for now to avoid breaking inline scripts/styles
# In a strict production environment, you should define a proper policy.
Talisman(app, content_security_policy=None)

# Register admin blueprint
from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html'), 500  # Reusing 404 template for simplicity, tailored message could be added

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['MAIL_RECIPIENT'] = os.getenv('MAIL_RECIPIENT')

# Blog configuration
app.config['BLOG_POSTS_DIR'] = os.getenv('BLOG_POSTS_DIR', 'blog_posts')

# Initialize Flask-Mail
mail = Mail(app)

# Helper function for loading JSON data (Moved up for DB initialization)
def load_json_data(filename, default=None):
    """Load data from a JSON file safely"""
    if default is None:
        default = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return default
    return default

# --- DATABASE MIGRATION HELPER ---
def init_db_data():
    """Populate DB with initial data if empty."""
    db.create_all()
    
    if not About.query.first():
        print("Initializing Database with default data...")
        
        # 1. Load existing JSON data for About
        about_data = load_json_data('about_info.json', {
            'intro': "Hello, I'm a Python Software Developer",
            'summary': "With over 10 years of experience...",
            'profile_image': '/static/images/about-me.png',
            'stats': {'projects': '50+', 'clients': '100+'},
            'skills': [],
            'experience': []
        })
        
        # Convert stats to int, handling '50+' string formats
        try:
            proj_count = int(str(about_data.get('stats', {}).get('projects', '0')).strip('+'))
        except:
            proj_count = 0
            
        new_about = About(
            intro=about_data.get('intro'),
            summary=about_data.get('summary'),
            profile_image=about_data.get('profile_image'),
            projects_completed=proj_count,
            years_experience=10, # Defaulting as requested
            skills_json=json.dumps(about_data.get('skills', [])),
            experience_json=json.dumps(about_data.get('experience', []))
        )
        db.session.add(new_about)
        
        # 2. Load Contact Info
        contact_data = load_json_data('contact_info.json', {'email': 'test@example.com'})
        new_contact = Contact(
            email=contact_data.get('email'),
            github=contact_data.get('github'),
            linkedin=contact_data.get('linkedin'),
            twitter=contact_data.get('twitter'),
            location=contact_data.get('location')
        )
        db.session.add(new_contact)
        
        # 3. Load Projects (Previously hardcoded in app.py)
        sample_projects = [
            {
                'title': 'Machine Learning Pipeline Framework',
                'description': 'A scalable ML pipeline framework built with Python for automated data processing, model training, and deployment.',
                'technologies': 'Python, TensorFlow, Docker, FastAPI',
                'category': 'Machine Learning',
                'github': 'https://github.com/username/ml-pipeline',
                'demo': 'https://demo.example.com',
                'image': '/static/images/ml-pipeline.jpg',
                'featured': True
            },
            {
                'title': 'RESTful API with Django',
                'description': 'Enterprise-grade REST API with authentication, rate limiting, and comprehensive documentation.',
                'technologies': 'Python, Django, PostgreSQL, Redis',
                'category': 'Web Development',
                'github': 'https://github.com/username/django-api',
                'demo': 'https://api.example.com',
                'image': '/static/images/django-api.jpg',
                'featured': True
            },
            {
                'title': 'Data Visualization Dashboard',
                'description': 'Interactive dashboard for real-time data visualization using Plotly and Dash.',
                'technologies': 'Python, Dash, Plotly, Pandas',
                'category': 'Data Science',
                'github': 'https://github.com/username/viz-dashboard',
                'demo': 'https://viz.example.com',
                'image': '/static/images/dashboard.jpg',
                'featured': False
            },
            {
                'title': 'Automated Testing Framework',
                'description': 'Comprehensive testing framework with CI/CD integration for Python applications.',
                'technologies': 'Python, Pytest, Selenium, GitHub Actions',
                'category': 'DevOps',
                'github': 'https://github.com/username/test-framework',
                'demo': None,
                'image': '/static/images/testing.jpg',
                'featured': False
            }
        ]
        
        for p in sample_projects:
            new_project = Project(
                title=p['title'],
                description=p['description'],
                technologies=p['technologies'],
                category=p['category'],
                github_url=p['github'],
                demo_url=p['demo'],
                image_url=p['image'],
                featured=p['featured']
            )
            db.session.add(new_project)
            
        db.session.commit()
        print("Database initialized successfully!")

with app.app_context():
    init_db_data()

@app.context_processor
def inject_global_data():
    """Inject contact and about info into all templates from DB"""
    contact = Contact.query.first()
    about = About.query.first()
    
    # Fallback objects if DB is empty/error (though init_db should handle it)
    if not contact:
        contact_info = {}
    else:
        contact_info = {
            'email': contact.email,
            'github': contact.github,
            'linkedin': contact.linkedin,
            'twitter': contact.twitter,
            'location': contact.location
        }
    
    if not about:
        about_info = {}
    else:
        # Parse JSON fields
        try:
            skills = json.loads(about.skills_json)
        except:
            skills = []
            
        try:
            exp = json.loads(about.experience_json)
        except:
            exp = []
            
        about_info = {
            'intro': about.intro,
            'summary': about.summary,
            'journey': about.journey if hasattr(about, 'journey') else "", # handling if field missing in older model vers
            'interests': about.interests if hasattr(about, 'interests') else "",
            'profile_image': about.profile_image,
            'stats': {
                'projects': about.projects_completed, 
                'years': about.years_experience,
                # 'clients' and 'certifications' removed as requested
            },
            'skills': skills,
            'experience': exp
        }
    
    return dict(
        contact_info=contact_info,
        about_info=about_info
    )

# Helper functions for markdown blog posts
def parse_markdown_file(filepath):
    """Parse a markdown file with YAML frontmatter"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract frontmatter
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        return None
    
    frontmatter_text, markdown_content = match.groups()
    
    # Parse frontmatter
    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Handle tags (comma-separated)
            if key == 'tags':
                metadata[key] = [tag.strip() for tag in value.split(',')]
            else:
                metadata[key] = value
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=[
        'fenced_code',
        'codehilite',
        'tables',
        'toc',
        'nl2br'
    ])
    html_content = md.convert(markdown_content)

    # Security: Sanitize HTML using bleach
    allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
        'p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
        'br', 'hr', 'pre', 'code', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 
        'img', 'a', 'ul', 'ol', 'li', 'blockquote', 'em', 'strong', 'i', 'b', 'del'
    ]
    allowed_attrs = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'target', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],
        'span': ['class'],
        'div': ['class']
    }
    html_content = bleach.clean(html_content, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    
    return {
        'metadata': metadata,
        'content': html_content,
        'raw_content': markdown_content
    }

def load_blog_posts():
    """Load all blog posts from markdown files"""
    posts = []
    blog_dir = app.config['BLOG_POSTS_DIR']
    
    if not os.path.exists(blog_dir):
        return []
    
    for filename in os.listdir(blog_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(blog_dir, filename)
            parsed = parse_markdown_file(filepath)
            
            if parsed:
                # Extract ID from filename (e.g., "1-title.md" -> 1)
                post_id = int(filename.split('-')[0])
                
                post = {
                    'id': post_id,
                    'title': parsed['metadata'].get('title', 'Untitled'),
                    'excerpt': parsed['metadata'].get('excerpt', ''),
                    'content': parsed['content'],
                    'author': parsed['metadata'].get('author', 'Unknown'),
                    'date': parsed['metadata'].get('date', ''),
                    'category': parsed['metadata'].get('category', 'Uncategorized'),
                    'tags': parsed['metadata'].get('tags', []),
                    'read_time': parsed['metadata'].get('read_time', '5 min'),
                    'image': parsed['metadata'].get('image', '/static/images/placeholder.jpg')
                }
                posts.append(post)
    
    # Sort by ID (newest first)
    posts.sort(key=lambda x: x['id'], reverse=True)
    return posts

# Load blog posts from markdown files
try:
    BLOG_POSTS = load_blog_posts()
except Exception as e:
    print(f"Error loading blog posts: {e}")
    BLOG_POSTS = []

# Sample data - In production, this would come from a database
# PROJECTS list migrated to database (see init_db_data)

RASPBERRY_PI_PROJECTS = [
    {
        'id': 1,
        'title': 'Smart Home Automation System',
        'description': 'Complete home automation solution using Raspberry Pi 4, controlling lights, temperature, and security cameras.',
        'hardware': ['Raspberry Pi 4', 'DHT22 Sensors', 'Relay Modules', 'Pi Camera'],
        'technologies': ['Python', 'Flask', 'MQTT', 'GPIO'],
        'features': [
            'Real-time temperature and humidity monitoring',
            'Remote control via web interface',
            'Motion detection and alerts',
            'Energy usage tracking'
        ],
        'github': 'https://github.com/username/smart-home',
        'image': '/static/images/smart-home.jpg'
    },
    {
        'id': 2,
        'title': 'IoT Weather Station',
        'description': 'Network-connected weather station collecting and visualizing environmental data.',
        'hardware': ['Raspberry Pi Zero W', 'BME280 Sensor', 'Rain Gauge', 'Anemometer'],
        'technologies': ['Python', 'InfluxDB', 'Grafana', 'I2C'],
        'features': [
            'Multi-sensor data collection',
            'Cloud data storage',
            'Historical data analysis',
            'API for third-party integration'
        ],
        'github': 'https://github.com/username/weather-station',
        'image': '/static/images/weather-station.jpg'
    },
    {
        'id': 3,
        'title': 'Raspberry Pi Cluster Computing',
        'description': 'Kubernetes cluster built with multiple Raspberry Pi units for distributed computing experiments.',
        'hardware': ['4x Raspberry Pi 4', 'Network Switch', 'Cluster Case'],
        'technologies': ['Python', 'Kubernetes', 'Docker', 'Ansible'],
        'features': [
            'Container orchestration',
            'Load balancing',
            'Automated deployment',
            'Monitoring and logging'
        ],
        'github': 'https://github.com/username/pi-cluster',
        'image': '/static/images/pi-cluster.jpg'
    }
]



PRODUCTS = [
    {
        'id': 1,
        'name': 'Python Mastery Course',
        'description': 'Comprehensive video course covering advanced Python concepts, design patterns, and real-world applications.',
        'price': 99.99,
        'type': 'digital',
        'category': 'Course',
        'features': [
            '50+ hours of video content',
            'Downloadable code examples',
            'Certificate of completion',
            'Lifetime access'
        ],
        'image': '/static/images/course-python.jpg',
        'available': True
    },
    {
        'id': 2,
        'name': 'Flask Project Templates',
        'description': 'Production-ready Flask application templates with authentication, API, and admin dashboard.',
        'price': 49.99,
        'type': 'digital',
        'category': 'Template',
        'features': [
            'Multiple template options',
            'Complete documentation',
            'Regular updates',
            'Email support'
        ],
        'image': '/static/images/flask-templates.jpg',
        'available': True
    },
    {
        'id': 3,
        'name': 'Raspberry Pi Starter Kit',
        'description': 'Curated hardware kit with sensors and components for Python IoT projects.',
        'price': 149.99,
        'type': 'physical',
        'category': 'Hardware',
        'features': [
            'Raspberry Pi 4 (4GB)',
            'Sensor collection',
            'Breadboard and jumper wires',
            'Getting started guide'
        ],
        'image': '/static/images/rpi-kit.jpg',
        'available': False
    },
    {
        'id': 4,
        'name': 'Python Code Review Service',
        'description': 'Professional code review service for your Python projects with detailed feedback and recommendations.',
        'price': 199.99,
        'type': 'service',
        'category': 'Service',
        'features': [
            'Comprehensive code analysis',
            'Security audit',
            'Performance recommendations',
            '1-hour consultation call'
        ],
        'image': '/static/images/code-review.jpg',
        'available': True
    }
]

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

    return render_template('index.html', 
                         featured_projects=featured_projects,
                         recent_posts=BLOG_POSTS[:3])

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
        'technologies': [t.strip() for t in project.technologies.split(',')] if project.technologies else [],
        'category': project.category,
        'image': project.image_url,
        'github': project.github_url,
        'demo': project.demo_url
    }
    
    return render_template('project_detail.html', project=p_dict)

@app.route('/raspberry-pi')
def raspberry_pi():
    """Raspberry Pi projects showcase"""
    return render_template('raspberry_pi.html', projects=RASPBERRY_PI_PROJECTS)

@app.route('/blog')
def blog():
    """Blog listing page"""
    return render_template('blog.html', posts=BLOG_POSTS)

@app.route('/blog/<int:post_id>')
def blog_post(post_id):
    """Individual blog post page"""
    post = next((p for p in BLOG_POSTS if p['id'] == post_id), None)
    if post:
        return render_template('blog_post.html', post=post)
    return "Post not found", 404

@app.route('/products')
def products():
    """E-commerce products page"""
    return render_template('products.html', products=PRODUCTS)

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
    
    filtered_posts = BLOG_POSTS
    
    if category:
        filtered_posts = [p for p in filtered_posts if p['category'] == category]
    
    if tag:
        filtered_posts = [p for p in filtered_posts if tag in p['tags']]
    
    return jsonify(filtered_posts)

@app.route('/api/contact', methods=['POST'])
def api_contact():
    """API endpoint for contact form submission"""
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
        
        # Extract form data
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')
        project_type = data.get('projectType', 'Not specified')
        
        # Create email message
        msg = Message(
            subject=f'Portfolio Contact: {subject}',
            recipients=[app.config['MAIL_RECIPIENT']],
            reply_to=email
        )
        
        # Email body
        msg.body = f"""
New contact form submission from your portfolio website:

Name: {name}
Email: {email}
Project Type: {project_type}

Subject: {subject}

Message:
{message}

---
This message was sent from your portfolio contact form.
        """
        
        msg.html = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c3e50;">New Contact Form Submission</h2>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
        <p><strong>Project Type:</strong> {project_type}</p>
    </div>
    
    <div style="margin: 20px 0;">
        <h3 style="color: #2c3e50;">Subject:</h3>
        <p>{subject}</p>
    </div>
    
    <div style="margin: 20px 0;">
        <h3 style="color: #2c3e50;">Message:</h3>
        <p style="white-space: pre-wrap;">{message}</p>
    </div>
    
    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
    <p style="color: #7f8c8d; font-size: 12px;">
        This message was sent from your portfolio contact form.
    </p>
</body>
</html>
        """
        
        # Send email
        mail.send(msg)
        
        return jsonify({
            'success': True,
            'message': 'Your message has been sent successfully!'
        }), 200
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send message. Please try again later.'
        }), 500

@app.template_filter('format_date')
def format_date(date_string):
    """Template filter for date formatting"""
    date = datetime.strptime(date_string, '%Y-%m-%d')
    return date.strftime('%B %d, %Y')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
