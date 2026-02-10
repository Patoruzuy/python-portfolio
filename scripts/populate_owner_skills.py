"""Populate owner profile with skills data"""
import sys
sys.path.insert(0, '/app')
from app import app, db, OwnerProfile
import json

with app.app_context():
    owner = OwnerProfile.query.first()
    
    if not owner:
        print("No owner profile found. Creating one...")
        owner = OwnerProfile(
            name="Sebastian Gomez",
            email="patoruzuy@tutanota.com",
            bio="Python Software Developer with 6 years of experience",
            github="https://github.com/Patoruzuy",
            linkedin="https://linkedin.com/in/sebastian-n-gomez",
            location="Irvine, North Ayrshire, Scotland, United Kingdom",
            years_experience=10,
            projects_completed=50,
            contributions="500+"
        )
        db.session.add(owner)
    
    # Update skills with proper data structure
    skills_data = [
        {
            "category": "Programming Languages",
            "icon": "fab fa-python",
            "skills": [
                {"name": "Python", "percent": 95},
                {"name": "JavaScript", "percent": 85},
                {"name": "TypeScript", "percent": 80},
                {"name": "SQL", "percent": 90},
                {"name": "Bash/Shell", "percent": 85}
            ]
        },
        {
            "category": "Frameworks & Libraries",
            "icon": "fas fa-layer-group",
            "skills": [
                {"name": "Flask", "percent": 95},
                {"name": "Django", "percent": 90},
                {"name": "FastAPI", "percent": 88},
                {"name": "SQLAlchemy", "percent": 92},
                {"name": "Celery", "percent": 85}
            ]
        },
        {
            "category": "Tools & Technologies",
            "icon": "fas fa-tools",
            "skills": [
                {"name": "Docker", "percent": 90},
                {"name": "Git", "percent": 95},
                {"name": "PostgreSQL", "percent": 88},
                {"name": "Redis", "percent": 85},
                {"name": "Linux", "percent": 90}
            ]
        }
    ]
    
    owner.skills_json = json.dumps(skills_data)
    
    # Update expertise if empty
    if not owner.expertise:
        expertise_data = [
            {
                "title": "Python Development",
                "icon": "fab fa-python",
                "description": "Expert in Python with frameworks like Flask, Django, and FastAPI",
                "file_name": "skill.py",
                "tags": ["Python", "Flask", "Django"]
            },
            {
                "title": "Raspberry Pi & IoT",
                "icon": "fas fa-microchip",
                "description": "Building IoT solutions and automation with Raspberry Pi",
                "file_name": "skill.py",
                "tags": ["IoT", "Hardware", "Sensors"]
            },
            {
                "title": "Machine Learning",
                "icon": "fas fa-brain",
                "description": "ML pipelines with TensorFlow, scikit-learn, and data analysis",
                "file_name": "skill.py",
                "tags": ["ML", "AI", "Data"]
            },
            {
                "title": "Database & APIs",
                "icon": "fas fa-database",
                "description": "RESTful APIs, PostgreSQL, Redis, and database optimization",
                "file_name": "skill.py",
                "tags": ["API", "SQL", "NoSQL"]
            },
            {
                "title": "DevOps & CI/CD",
                "icon": "fas fa-code-branch",
                "description": "Docker, GitHub Actions, automated testing and deployment",
                "file_name": "skill.py",
                "tags": ["Docker", "CI/CD", "Automation"]
            },
            {
                "title": "Data Science",
                "icon": "fas fa-chart-line",
                "description": "Data visualization with Plotly, Dash, and Pandas",
                "file_name": "skill.py",
                "tags": ["Plotly", "Pandas", "Viz"]
            }
        ]
        owner.expertise_json = json.dumps(expertise_data)
    
    db.session.commit()
    
    print("✅ Owner profile updated successfully!")
    print(f"Name: {owner.name}")
    print(f"Skills categories: {len(owner.skills)}")
    for category in owner.skills:
        print(f"  - {category['category']}: {len(category['skills'])} skills")
    print(f"Expertise items: {len(owner.expertise)}")
