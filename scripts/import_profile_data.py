"""
Import profile data from JSON files to database
"""
import sys
import os
from pathlib import Path
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import OwnerProfile
import json


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / 'data'


def resolve_profile_data_file(filename: str) -> Optional[Path]:
    """
    Resolve profile JSON file from preferred and legacy locations.

    Preferred location:
    - data/<filename>
    Legacy fallback:
    - <repo_root>/<filename>
    """
    candidates = [
        DATA_DIR / filename,
        REPO_ROOT / filename
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def import_profile_data():
    """Import profile data from about_info.json and contact_info.json"""
    print("👤 Importing profile data...")
    
    with app.app_context():
        # Check if profile already exists
        existing_profile = OwnerProfile.query.first()
        
        # Resolve source JSON files (supports both new and legacy layouts)
        about_path = resolve_profile_data_file('about_info.json')
        if about_path is None:
            print("❌ about_info.json not found in data/ or repository root")
            return
        
        contact_path = resolve_profile_data_file('contact_info.json')
        if contact_path is None:
            print("❌ contact_info.json not found in data/ or repository root")
            return
        
        with about_path.open('r', encoding='utf-8') as f:
            about_data = json.load(f)
        
        with contact_path.open('r', encoding='utf-8') as f:
            contact_data = json.load(f)
        
        if existing_profile:
            print("📝 Updating existing profile...")
            profile = existing_profile
        else:
            print("✨ Creating new profile...")
            profile = OwnerProfile()
        
        # Basic info
        profile.name = "Sebastian Gomez"
        profile.title = about_data.get('intro', 'Python Software Developer')
        profile.bio = about_data.get('summary', '')
        profile.profile_image = about_data.get('profile_image', '/static/images/about-me.png')
        
        # Contact info
        profile.email = contact_data.get('email', '')
        profile.github = contact_data.get('github', '')
        profile.linkedin = contact_data.get('linkedin', '')
        profile.twitter = contact_data.get('twitter', '')
        profile.location = contact_data.get('location', '')
        
        # About sections (correct field names from model)
        profile.intro = about_data.get('intro', '')
        profile.summary = about_data.get('summary', '')
        profile.journey = about_data.get('journey', '')
        profile.interests = about_data.get('interests', '')
        
        # Stats (convert from string format like "50+" to integers for numeric fields)
        stats = about_data.get('stats', {})
        # Extract numbers from strings like "6+" -> 6
        def extract_number(value):
            import re
            match = re.search(r'\d+', str(value))
            return int(match.group()) if match else 0
        
        profile.years_experience = extract_number(stats.get('years_experience', '6+'))
        profile.projects_completed = extract_number(stats.get('projects', '50+'))
        profile.contributions = extract_number(stats.get('contributions', '500+'))
        profile.clients_served = extract_number(stats.get('clients', '100+'))
        profile.certifications = extract_number(stats.get('certifications', '15+'))
        
        # Skills and Experience as JSON
        profile.skills_json = json.dumps(about_data.get('skills', []))
        profile.experience_json = json.dumps(about_data.get('experience', []))
        
        if not existing_profile:
            db.session.add(profile)
        
        db.session.commit()
        
        print("\n✅ Profile data imported successfully!")
        print(f"   Name: {profile.name}")
        print(f"   Email: {profile.email}")
        print(f"   GitHub: {profile.github}")
        print(f"   LinkedIn: {profile.linkedin}")
        print(f"   Location: {profile.location}")

if __name__ == '__main__':
    import_profile_data()
