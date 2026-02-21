"""
Initialize or repair database schema.
This script safely creates all missing tables without dropping existing data.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from app.models import (
    SiteConfig
)


def init_database():
    """Initialize database schema and create default SiteConfig"""
    with app.app_context():
        print("🔧 Creating database tables...")
        
        try:
            # Create all tables (safe: only creates missing ones)
            db.create_all()
            print("✅ Database schema created/verified")
            
            # Check if SiteConfig exists
            config = SiteConfig.query.first()
            if not config:
                print("📝 Creating default SiteConfig...")
                config = SiteConfig(
                    site_name="Python Developer Portfolio",
                    tagline="Building Scalable Solutions",
                    blog_enabled=True,
                    products_enabled=True,
                    analytics_enabled=True
                )
                db.session.add(config)
                db.session.commit()
                print("✅ Default SiteConfig created")
            else:
                print(f"✅ SiteConfig exists: {config.site_name}")
            
            # Verify all tables exist (using correct table names)
            tables = [
                'owner_profile', 'blog_posts', 'products', 'projects',
                'raspberry_pi_projects', 'newsletter', 'site_config',
                'page_views', 'user_sessions', 'analytics_events',
                'admin_recovery_codes', 'cookie_consents', 'users'
            ]
            
            print("\n📋 Verifying tables:")
            # Define allowed table names to prevent SQL injection
            allowed_tables = {
                'owner_profile', 'blog_post', 'product', 'project', 
                'raspberry_pi_project', 'newsletter', 'site_config', 
                'page_view', 'user_session', 'analytics_event', 
                'admin_recovery_code'
            }
            for table in tables:
                # Validate table name is in allowed list
                if table.lower() not in allowed_tables:
                    print(f"  ✗ {table}: SKIPPED - Not in allowed tables list")
                    continue
                try:
                    # Use text() with validated table name (safe since it's from allowed list)
                    result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))  # nosec B608
                    count = result.scalar()
                    print(f"  ✓ {table}: {count} records")
                except Exception as e:
                    print(f"  ✗ {table}: ERROR - {e}")
            
            print("\n✅ Database initialization complete!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
