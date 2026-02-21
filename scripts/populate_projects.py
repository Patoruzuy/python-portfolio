"""
Populate sample projects into the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import Project
from datetime import datetime, timezone

def populate_projects():
    """Add sample projects to database"""
    print("📊 Populating sample projects...")
    
    with app.app_context():
        # Check if projects already exist
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
                'featured': True
            },
            {
                'title': 'API Management System',
                'description': 'RESTful API with authentication, rate limiting, and comprehensive documentation.',
                'image_url': '/static/images/api.jpg',
                'category': 'API Development',
                'technologies': 'Python, FastAPI, PostgreSQL, JWT',
                'github_url': 'https://github.com/username/api',
                'demo_url': '',
                'featured': False
            },
            {
                'title': 'Machine Learning Pipeline',
                'description': 'End-to-end ML pipeline for training, deploying, and monitoring machine learning models.',
                'image_url': '/static/images/ml.jpg',
                'category': 'Machine Learning',
                'technologies': 'Python, scikit-learn, TensorFlow, Docker',
                'github_url': 'https://github.com/username/ml-pipeline',
                'demo_url': '',
                'featured': False
            }
        ]
        
        for project_data in sample_projects:
            project = Project(**project_data)
            db.session.add(project)
        
        db.session.commit()
        print(f"✅ Added {len(sample_projects)} projects successfully!")

if __name__ == '__main__':
    populate_projects()
