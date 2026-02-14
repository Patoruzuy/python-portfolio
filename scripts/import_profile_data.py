"""
Import profile data from JSON files to database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import OwnerProfile
import json

def import_profile_data():
    """Import profile data from about_info.json and contact_info.json"""
    print("👤 Importing profile data...")
    
    with app.app_context():
        # Check if profile already exists
        existing_profile = OwnerProfile.query.first()
        
        # Load JSON files
        if not os.path.exists('about_info.json'):
            print("❌ about_info.json not found")
            return
        
        if not os.path.exists('contact_info.json'):
            print("❌ contact_info.json not found")
            return
        
        with open('about_info.json', 'r', encoding='utf-8') as f:
            about_data = json.load(f)
        
        with open('contact_info.json', 'r', encoding='utf-8') as f:
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
        
        # About sections
        profile.about_intro = about_data.get('intro', '')
        profile.about_summary = about_data.get('summary', '')
        profile.about_journey = about_data.get('journey', '')
        profile.about_interests = about_data.get('interests', '')
        
        # Stats
        stats = about_data.get('stats', {})
        profile.stats_projects = stats.get('projects', '50+')
        profile.stats_clients = stats.get('clients', '100+')
        profile.stats_certifications = stats.get('certifications', '15+')
        profile.stats_years_experience = stats.get('years_experience', '6+')
        profile.stats_contributions = stats.get('contributions', '500+')
        
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
