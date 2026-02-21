"""
Data Migration Script: Old Schema → New Schema
Migrates data from About/Contact models to OwnerProfile,
hardcoded lists to DB models, and markdown files to BlogPost model.

Run this ONCE after deploying new models.
"""

from app import app
from app.models import (
    db, OwnerProfile, SiteConfig, Product, RaspberryPiProject, 
    BlogPost, About, Contact
)
from slugify import slugify
import os
import json
import markdown
import re


def migrate_owner_profile():
    """Migrate About + Contact → OwnerProfile"""
    print("📊 Migrating owner profile...")
    
    # Check if already migrated
    if OwnerProfile.query.first():
        print("✅ OwnerProfile already exists, skipping...")
        return
    
    about = About.query.first()
    contact = Contact.query.first()
    
    # Load about_info.json if exists (for skills/experience data)
    about_json = {}
    if os.path.exists('about_info.json'):
        with open('about_info.json', 'r', encoding='utf-8') as f:
            about_json = json.load(f)
    
    owner = OwnerProfile(
        name="Sebastian Gomez",  # Update with real name
        title="Python Software Developer",
        bio=about.summary if about else "",
        profile_image=about.profile_image if about else '/static/images/profile.jpg',
        
        # Contact info
        email=contact.email if contact else "",
        github=contact.github if contact else "",
        linkedin=contact.linkedin if contact else "",
        twitter=contact.twitter if contact else "",
        location=contact.location if contact else "",
        
        # About content
        intro=about.intro if about else "",
        summary=about.summary if about else "",
        journey=about_json.get('journey', ''),
        interests=about_json.get('interests', ''),
        
        # Stats
        years_experience=about.years_experience if about else 10,
        projects_completed=about.projects_completed if about else 50,
        contributions=about_json.get('stats', {}).get('contributions', 500),
        clients_served=about_json.get('stats', {}).get('clients', 25),
        certifications=about_json.get('stats', {}).get('certifications', 5),
        
        # JSON data
        skills_json=about.skills_json if about else json.dumps(about_json.get('skills', [])),
        experience_json=about.experience_json if about else json.dumps(about_json.get('experience', [])),
        
        # Homepage expertise cards (6 cards)
        expertise_json=json.dumps([
            {
                "title": "Python Development",
                "icon": "fab fa-python",
                "description": "Expert in Python with frameworks like Flask, Django, and FastAPI"
            },
            {
                "title": "Raspberry Pi & IoT",
                "icon": "fas fa-microchip",
                "description": "Building IoT solutions and automation with Raspberry Pi"
            },
            {
                "title": "Machine Learning",
                "icon": "fas fa-brain",
                "description": "ML pipelines with TensorFlow, scikit-learn, and data analysis"
            },
            {
                "title": "Database & APIs",
                "icon": "fas fa-database",
                "description": "RESTful APIs, PostgreSQL, Redis, and database optimization"
            },
            {
                "title": "DevOps & CI/CD",
                "icon": "fas fa-code-branch",
                "description": "Docker, GitHub Actions, automated testing and deployment"
            },
            {
                "title": "Data Science",
                "icon": "fas fa-chart-line",
                "description": "Data visualization with Plotly, Dash, and Pandas"
            }
        ])
    )
    
    db.session.add(owner)
    db.session.commit()
    print("✅ OwnerProfile created successfully")


def migrate_site_config():
    """Create default SiteConfig"""
    print("⚙️  Creating site configuration...")
    
    if SiteConfig.query.first():
        print("✅ SiteConfig already exists, skipping...")
        return
    
    config = SiteConfig(
        site_name="Python Developer Portfolio",
        tagline="Building scalable solutions with Python",
        mail_server=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
        mail_port=int(os.getenv('MAIL_PORT', 587)),
        mail_use_tls=True,
        mail_username=os.getenv('MAIL_USERNAME'),
        mail_default_sender=os.getenv('MAIL_DEFAULT_SENDER'),
        mail_recipient=os.getenv('MAIL_RECIPIENT'),
        blog_enabled=True,
        products_enabled=True,
        analytics_enabled=True
    )
    
    db.session.add(config)
    db.session.commit()
    print("✅ SiteConfig created successfully")


def migrate_products():
    """Migrate hardcoded PRODUCTS list to DB"""
    print("🛒 Migrating products...")
    
    if Product.query.first():
        print("✅ Products already exist, skipping...")
        return
    
    products_data = [
        {
            'name': 'Python Mastery Course',
            'description': 'Comprehensive video course covering advanced Python concepts, design patterns, and real-world applications.',
            'price': 99.99,
            'type': 'digital',
            'category': 'Course',
            'features': ['50+ hours of video content', 'Downloadable code examples', 'Certificate of completion', 'Lifetime access'],
            'technologies': 'Python, Flask, Django, FastAPI',
            'purchase_link': None,
            'demo_link': None,
            'image': '/static/images/course-python.jpg',
            'available': True
        },
        {
            'name': 'Flask Project Templates',
            'description': 'Production-ready Flask application templates with authentication, API, and admin dashboard.',
            'price': 49.99,
            'type': 'digital',
            'category': 'Template',
            'features': ['Multiple template options', 'Complete documentation', 'Regular updates', 'Email support'],
            'technologies': 'Flask, SQLAlchemy, Bootstrap',
            'purchase_link': None,
            'demo_link': None,
            'image': '/static/images/flask-templates.jpg',
            'available': True
        },
        {
            'name': 'Raspberry Pi Starter Kit',
            'description': 'Curated hardware kit with sensors and components for Python IoT projects.',
            'price': 149.99,
            'type': 'physical',
            'category': 'Hardware',
            'features': ['Raspberry Pi 4 (4GB)', 'Sensor collection', 'Breadboard and jumper wires', 'Getting started guide'],
            'technologies': 'Python, GPIO, I2C',
            'purchase_link': None,
            'demo_link': None,
            'image': '/static/images/rpi-kit.jpg',
            'available': False
        },
        {
            'name': 'Python Code Review Service',
            'description': 'Professional code review service for your Python projects with detailed feedback and recommendations.',
            'price': 199.99,
            'type': 'service',
            'category': 'Service',
            'features': ['Comprehensive code analysis', 'Security audit', 'Performance recommendations', '1-hour consultation call'],
            'technologies': 'Python, Static Analysis, Security',
            'purchase_link': None,
            'demo_link': None,
            'image': '/static/images/code-review.jpg',
            'available': True
        }
    ]
    
    for p in products_data:
        product = Product(
            name=p['name'],
            description=p['description'],
            price=p['price'],
            type=p['type'],
            category=p['category'],
            features_json=json.dumps(p['features']),
            technologies=p['technologies'],
            purchase_link=p['purchase_link'],
            demo_link=p['demo_link'],
            image_url=p['image'],
            available=p['available']
        )
        db.session.add(product)
    
    db.session.commit()
    print(f"✅ Migrated {len(products_data)} products")


def migrate_raspberry_pi_projects():
    """Migrate hardcoded RASPBERRY_PI_PROJECTS list to DB"""
    print("🍓 Migrating Raspberry Pi projects...")
    
    if RaspberryPiProject.query.first():
        print("✅ Raspberry Pi projects already exist, skipping...")
        return
    
    rpi_data = [
        {
            'title': 'Smart Home Automation System',
            'description': 'Complete home automation solution using Raspberry Pi 4, controlling lights, temperature, and security cameras.',
            'hardware': ['Raspberry Pi 4', 'DHT22 Sensors', 'Relay Modules', 'Pi Camera'],
            'technologies': 'Python, Flask, MQTT, GPIO',
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
            'title': 'IoT Weather Station',
            'description': 'Network-connected weather station collecting and visualizing environmental data.',
            'hardware': ['Raspberry Pi Zero W', 'BME280 Sensor', 'Rain Gauge', 'Anemometer'],
            'technologies': 'Python, InfluxDB, Grafana, I2C',
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
            'title': 'Raspberry Pi Cluster Computing',
            'description': 'Kubernetes cluster built with multiple Raspberry Pi units for distributed computing experiments.',
            'hardware': ['4x Raspberry Pi 4', 'Network Switch', 'Cluster Case'],
            'technologies': 'Python, Kubernetes, Docker, Ansible',
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
    
    for rpi in rpi_data:
        project = RaspberryPiProject(
            title=rpi['title'],
            description=rpi['description'],
            hardware_json=json.dumps(rpi['hardware']),
            technologies=rpi['technologies'],
            features_json=json.dumps(rpi['features']),
            github_url=rpi['github'],
            image_url=rpi['image']
        )
        db.session.add(project)
    
    db.session.commit()
    print(f"✅ Migrated {len(rpi_data)} Raspberry Pi projects")


def parse_markdown_frontmatter(content):
    """Parse YAML frontmatter from markdown content"""
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return {}, content
    
    frontmatter_text = match.group(1)
    markdown_content = match.group(2)
    
    # Simple YAML parser (for our basic use case)
    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()
    
    return metadata, markdown_content


def migrate_blog_posts():
    """Migrate markdown blog posts from files to DB"""
    print("📝 Migrating blog posts...")
    
    if BlogPost.query.first():
        print("✅ Blog posts already exist, skipping...")
        return
    
    blog_dir = 'blog_posts'
    if not os.path.exists(blog_dir):
        print("⚠️  No blog_posts directory found, skipping...")
        return
    
    migrated = 0
    for filename in os.listdir(blog_dir):
        if not filename.endswith('.md'):
            continue
        
        filepath = os.path.join(blog_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata, markdown_content = parse_markdown_frontmatter(content)
        
        # Extract ID from filename (e.g., "1-title.md" → 1)
        try:
            post_id = int(filename.split('-')[0])
        except:
            post_id = None
        
        title = metadata.get('title', 'Untitled')
        slug = slugify(title)
        
        # Calculate read time (avg 200 words per minute)
        word_count = len(markdown_content.split())
        read_time = max(1, round(word_count / 200))
        
        post = BlogPost(
            id=post_id,  # Use original ID if available
            title=title,
            slug=slug,
            excerpt=metadata.get('excerpt', ''),
            author=metadata.get('author', 'Admin'),
            content=markdown_content,
            category=metadata.get('category', 'Tutorial'),
            tags=metadata.get('tags', ''),
            image_url=metadata.get('image', '/static/images/blog-placeholder.jpg'),
            read_time=read_time,
            published=True
        )
        
        db.session.add(post)
        migrated += 1
    
    db.session.commit()
    print(f"✅ Migrated {migrated} blog posts")


def main():
    """Run all migrations"""
    with app.app_context():
        print("🚀 Starting data migration...\n")
        
        # Create all new tables
        db.create_all()
        print("✅ Database tables created\n")
        
        # Run migrations
        migrate_owner_profile()
        migrate_site_config()
        migrate_products()
        migrate_raspberry_pi_projects()
        migrate_blog_posts()
        
        print("\n✨ Migration complete! You can now:")
        print("   1. Test the application")
        print("   2. Drop old tables: About, Contact")
        print("   3. Remove hardcoded PRODUCTS and RASPBERRY_PI_PROJECTS from app.py")
        print("   4. Delete markdown files from blog_posts/ directory")


if __name__ == '__main__':
    main()
