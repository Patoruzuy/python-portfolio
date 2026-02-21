import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import BlogPost, OwnerProfile, SiteConfig

with app.app_context():
    print(f'✅ Blog Posts: {BlogPost.query.count()}')
    print(f'✅ Owner Profiles: {OwnerProfile.query.count()}')
    print(f'✅ SiteConfig: {SiteConfig.query.count()}')
    print(f'\n📊 Database verified successfully!')
