"""
Populate sample data for Products, Projects, Blog Posts, and Raspberry Pi Projects
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import Product, Project, BlogPost, RaspberryPiProject
from datetime import datetime, timezone
import json

def populate_products():
    """Add sample products to database"""
    print("🛒 Populating products...")
    
    with app.app_context():
        if Product.query.count() > 0:
            print(f"✅ {Product.query.count()} products already exist")
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
        print(f"✅ Added {len(products_data)} products")

def populate_projects():
    """Add sample projects to database"""
    print("📊 Populating projects...")
    
    with app.app_context():
        if Project.query.count() > 0:
            print(f"✅ {Project.query.count()} projects already exist")
            return
        
        sample_projects = [
            {
                'title': 'E-Commerce Platform',
                'description': 'Full-stack e-commerce solution with payment integration, inventory management, and real-time analytics.',
                'image_url': '/static/images/ecommerce.jpg',
                'category': 'Web Development',
                'technologies': 'Python, Flask, PostgreSQL, Redis, Stripe API',
                'github_url': 'https://github.com/username/ecommerce',
                'demo_url': '',
                'featured': True
            },
            {
                'title': 'Real-Time Chat Application',
                'description': 'WebSocket-based chat application with user authentication, private messaging, and group chat functionality.',
                'image_url': '/static/images/chat-app.jpg',
                'category': 'Web Development',
                'technologies': 'Python, Flask, Socket.IO, Redis',
                'github_url': 'https://github.com/username/chat-app',
                'demo_url': '',
                'featured': True
            },
            {
                'title': 'Data Visualization Dashboard',
                'description': 'Interactive dashboard for visualizing complex datasets with real-time updates and export functionality.',
                'image_url': '/static/images/dashboard.jpg',
                'category': 'Data Science',
                'technologies': 'Python, Plotly, Dash, Pandas',
                'github_url': 'https://github.com/username/dashboard',
                'demo_url': '',
                'featured': False
            },
            {
                'title': 'ML Model Deployment Pipeline',
                'description': 'Automated pipeline for training, versioning, and deploying machine learning models with A/B testing.',
                'image_url': '/static/images/ml-pipeline.jpg',
                'category': 'Machine Learning',
                'technologies': 'Python, TensorFlow, Docker, Kubernetes',
                'github_url': 'https://github.com/username/ml-pipeline',
                'demo_url': '',
                'featured': True
            },
            {
                'title': 'RESTful API Framework',
                'description': 'Scalable API framework with authentication, rate limiting, and comprehensive documentation.',
                'image_url': '/static/images/django-api.jpg',
                'category': 'Backend',
                'technologies': 'Python, Django, DRF, PostgreSQL',
                'github_url': 'https://github.com/username/api-framework',
                'demo_url': '',
                'featured': False
            },
            {
                'title': 'Automated Testing Suite',
                'description': 'Comprehensive testing framework with unit, integration, and E2E tests with CI/CD integration.',
                'image_url': '/static/images/testing.jpg',
                'category': 'DevOps',
                'technologies': 'Python, Pytest, Selenium, GitHub Actions',
                'github_url': 'https://github.com/username/testing-suite',
                'demo_url': '',
                'featured': False
            }
        ]
        
        for proj in sample_projects:
            project = Project(
                title=proj['title'],
                description=proj['description'],
                image_url=proj['image_url'],
                category=proj['category'],
                technologies=proj['technologies'],
                github_url=proj['github_url'],
                demo_url=proj['demo_url'],
                featured=proj['featured']
            )
            db.session.add(project)
        
        db.session.commit()
        print(f"✅ Added {len(sample_projects)} projects")

def populate_raspberry_pi_projects():
    """Add sample Raspberry Pi projects to database"""
    print("🍓 Populating Raspberry Pi projects...")
    
    with app.app_context():
        if RaspberryPiProject.query.count() > 0:
            print(f"✅ {RaspberryPiProject.query.count()} Raspberry Pi projects already exist")
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
                    'Weather forecasting'
                ],
                'github': 'https://github.com/username/weather-station',
                'image': '/static/images/weather-station.jpg'
            },
            {
                'title': 'Raspberry Pi Cluster',
                'description': 'High-performance computing cluster using multiple Raspberry Pis for distributed computing tasks.',
                'hardware': ['4x Raspberry Pi 4', 'Network Switch', 'Cluster Case', 'Cooling Fans'],
                'technologies': 'Python, MPI, Docker Swarm, Kubernetes',
                'features': [
                    'Parallel processing capabilities',
                    'Container orchestration',
                    'Load balancing',
                    'Distributed storage'
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
        print(f"✅ Added {len(rpi_data)} Raspberry Pi projects")

def populate_blog_posts():
    """Add sample blog posts to database"""
    print("📝 Populating blog posts...")
    
    with app.app_context():
        if BlogPost.query.count() > 0:
            print(f"✅ {BlogPost.query.count()} blog posts already exist")
            return
        
        blog_posts = [
            {
                'title': 'Getting Started with Flask: A Comprehensive Guide',
                'content': '''
# Getting Started with Flask

Flask is a lightweight WSGI web application framework written in Python. It's designed to make getting started quick and easy, with the ability to scale up to complex applications.

## Why Flask?

- **Lightweight and modular**: Flask has a small core and is easily extendable
- **Well-documented**: Extensive documentation and large community
- **Flexible**: No particular way of doing things is enforced
- **Great for APIs**: Perfect for building RESTful APIs

## Installation

```python
pip install Flask
```

## Your First Flask App

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
```

This is just the beginning of your Flask journey!
                ''',
                'category': 'Tutorial',
                'tags': ['Python', 'Flask', 'Web Development']
            },
            {
                'title': 'Building RESTful APIs with Python',
                'content': '''
# Building RESTful APIs with Python

REST (Representational State Transfer) is an architectural style for designing networked applications. Let's explore how to build robust APIs with Python.

## Key Principles

1. **Stateless**: Each request contains all necessary information
2. **Client-Server**: Separation of concerns
3. **Cacheable**: Responses must define themselves as cacheable or not
4. **Uniform Interface**: Standardized way of communication

## Example with Flask

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify({'users': []})

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    return jsonify(data), 201
```

Building RESTful APIs is an essential skill for modern web development!
                ''',
                'category': 'Backend',
                'tags': ['Python', 'API', 'REST', 'Flask']
            },
            {
                'title': 'Introduction to Machine Learning with Python',
                'content': '''
# Introduction to Machine Learning with Python

Machine Learning is transforming how we solve complex problems. Python has become the de facto language for ML thanks to its rich ecosystem.

## Popular Libraries

- **NumPy**: Numerical computing
- **Pandas**: Data manipulation
- **Scikit-learn**: Machine learning algorithms
- **TensorFlow/PyTorch**: Deep learning

## Simple Example

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

# Prepare data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)
```

Start your ML journey today!
                ''',
                'category': 'Machine Learning',
                'tags': ['Python', 'Machine Learning', 'Data Science', 'AI']
            },
            {
                'title': 'Deploying Python Applications with Docker',
                'content': '''
# Deploying Python Applications with Docker

Docker makes it easy to package and deploy Python applications with all their dependencies.

## Why Docker?

- **Consistency**: Same environment everywhere
- **Isolation**: Each container is isolated
- **Portability**: Run anywhere Docker is supported
- **Scalability**: Easy to scale horizontally

## Sample Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
```

## Docker Compose

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
  redis:
    image: redis:alpine
```

Containerization is the future of deployment!
                ''',
                'category': 'DevOps',
                'tags': ['Docker', 'Python', 'DevOps', 'Deployment']
            }
        ]
        
        from slugify import slugify
        
        for post_data in blog_posts:
            post = BlogPost(
                title=post_data['title'],
                slug=slugify(post_data['title']),
                content=post_data['content'],
                excerpt=post_data['content'][:200] + '...',
                author='Sebastian Gomez',
                category=post_data['category'],
                tags=', '.join(post_data['tags']),
                published=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(post)
        
        db.session.commit()
        print(f"✅ Added {len(blog_posts)} blog posts")

if __name__ == '__main__':
    print("🚀 Starting database population...\n")
    
    populate_products()
    populate_projects()
    populate_raspberry_pi_projects()
    populate_blog_posts()
    
    print("\n✅ Database population complete!")
