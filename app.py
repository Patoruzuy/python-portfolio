"""
Python Developer Portfolio Website
A Flask-based portfolio showcasing Python projects, Raspberry Pi implementations,
technical blog, and e-commerce capabilities.
"""

from flask import Flask, render_template, jsonify, request
from flask_mail import Mail, Message
from datetime import datetime
import json
import os
import markdown
import re
from dotenv import load_dotenv
from markupsafe import Markup

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

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
PROJECTS = [
    {
        'id': 1,
        'title': 'Machine Learning Pipeline Framework',
        'description': 'A scalable ML pipeline framework built with Python for automated data processing, model training, and deployment.',
        'technologies': ['Python', 'TensorFlow', 'Docker', 'FastAPI'],
        'category': 'Machine Learning',
        'github': 'https://github.com/username/ml-pipeline',
        'demo': 'https://demo.example.com',
        'image': '/static/images/ml-pipeline.jpg',
        'featured': True
    },
    {
        'id': 2,
        'title': 'RESTful API with Django',
        'description': 'Enterprise-grade REST API with authentication, rate limiting, and comprehensive documentation.',
        'technologies': ['Python', 'Django', 'PostgreSQL', 'Redis'],
        'category': 'Web Development',
        'github': 'https://github.com/username/django-api',
        'demo': 'https://api.example.com',
        'image': '/static/images/django-api.jpg',
        'featured': True
    },
    {
        'id': 3,
        'title': 'Data Visualization Dashboard',
        'description': 'Interactive dashboard for real-time data visualization using Plotly and Dash.',
        'technologies': ['Python', 'Dash', 'Plotly', 'Pandas'],
        'category': 'Data Science',
        'github': 'https://github.com/username/viz-dashboard',
        'demo': 'https://viz.example.com',
        'image': '/static/images/dashboard.jpg',
        'featured': False
    },
    {
        'id': 4,
        'title': 'Automated Testing Framework',
        'description': 'Comprehensive testing framework with CI/CD integration for Python applications.',
        'technologies': ['Python', 'Pytest', 'Selenium', 'GitHub Actions'],
        'category': 'DevOps',
        'github': 'https://github.com/username/test-framework',
        'demo': None,
        'image': '/static/images/testing.jpg',
        'featured': False
    }
]

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
    featured_projects = [p for p in PROJECTS if p.get('featured', False)]
    return render_template('index.html', 
                         featured_projects=featured_projects,
                         recent_posts=BLOG_POSTS[:3])

@app.route('/projects')
def projects():
    """Projects showcase page"""
    return render_template('projects.html', projects=PROJECTS)

@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    """Individual project detail page"""
    project = next((p for p in PROJECTS if p['id'] == project_id), None)
    if project:
        return render_template('project_detail.html', project=project)
    return "Project not found", 404

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
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')


# API endpoints for dynamic filtering
@app.route('/api/projects')
def api_projects():
    """API endpoint for project filtering"""
    category = request.args.get('category')
    technology = request.args.get('technology')
    
    filtered_projects = PROJECTS
    
    if category:
        filtered_projects = [p for p in filtered_projects if p['category'] == category]
    
    if technology:
        filtered_projects = [p for p in filtered_projects 
                           if technology in p['technologies']]
    
    return jsonify(filtered_projects)

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
