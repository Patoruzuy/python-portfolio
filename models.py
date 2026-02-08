from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    # Storing list as comma-separated string for simplicity in SQLite 
    # (or use valid JSON type if using PostgreSQL, but Text is safer for SQLite compat)
    technologies = db.Column(db.String(200), nullable=False) 
    category = db.Column(db.String(50), nullable=False)
    github_url = db.Column(db.String(200))
    demo_url = db.Column(db.String(200))
    image_url = db.Column(db.String(200), default='/static/images/placeholder.jpg')
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Basic Info
    intro = db.Column(db.String(200))
    summary = db.Column(db.Text)
    profile_image = db.Column(db.String(200))
    
    # Stats (Centralized)
    years_experience = db.Column(db.Integer, default=0)
    projects_completed = db.Column(db.Integer, default=0)
    # Removed clients/contributions as requested
    
    # Large text fields for storing JSON strings of skills/experience
    skills_json = db.Column(db.Text, default='[]')
    experience_json = db.Column(db.Text, default='[]')
    
    @property
    def skills(self):
        import json
        try:
            return json.loads(self.skills_json) if self.skills_json else []
        except:
            return []

    @property
    def experience(self):
        import json
        try:
            return json.loads(self.experience_json) if self.experience_json else []
        except:
            return []

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    github = db.Column(db.String(100))
    linkedin = db.Column(db.String(100))
    twitter = db.Column(db.String(100))
    location = db.Column(db.String(100))
