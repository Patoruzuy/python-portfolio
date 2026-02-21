"""
Database migration script to add new models and update existing ones.
Adds: Newsletter, User models
Updates: Product model with payment fields
Removes: About, Contact models (deprecated)

Run this after updating models.py to sync the database.
"""
from typing import Optional
from app import app, db
from app.models import Newsletter, User, Product
from sqlalchemy import inspect, text
import os

def backup_database() -> Optional[str]:
    """Create backup of current database"""
    if os.path.exists('portfolio.db'):
        import shutil
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'backups/portfolio_{timestamp}.db'
        os.makedirs('backups', exist_ok=True)
        shutil.copy2('portfolio.db', backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    return None

def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def table_exists(table_name: str) -> bool:
    """Check if a table exists"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def migrate() -> None:
    """Run migration"""
    print("🔄 Starting database migration...")
    
    with app.app_context():
        # Backup database first
        backup_database()
        
        # 1. Create new tables if they don't exist
        print("\n📦 Creating new tables...")
        
        if not table_exists('newsletter'):
            print("  ➕ Creating newsletter table...")
            db.session.execute(text('''
                CREATE TABLE newsletter (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    active BOOLEAN DEFAULT 1,
                    confirmed BOOLEAN DEFAULT 0,
                    confirmation_token VARCHAR(100) UNIQUE,
                    subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    unsubscribed_at DATETIME
                )
            '''))
            db.session.execute(text('CREATE INDEX ix_newsletter_email ON newsletter (email)'))
            db.session.execute(text('CREATE INDEX ix_newsletter_active ON newsletter (active)'))
            print("     ✅ Newsletter table created")
        else:
            print("     ⏭️  Newsletter table already exists")
        
        if not table_exists('users'):
            print("  ➕ Creating users table...")
            db.session.execute(text('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    is_active BOOLEAN DEFAULT 1,
                    is_superuser BOOLEAN DEFAULT 0,
                    reset_token VARCHAR(100) UNIQUE,
                    reset_token_expiry DATETIME,
                    last_login DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            '''))
            db.session.execute(text('CREATE INDEX ix_users_username ON users (username)'))
            db.session.execute(text('CREATE INDEX ix_users_email ON users (email)'))
            db.session.execute(text('CREATE INDEX ix_users_is_active ON users (is_active)'))
            print("     ✅ Users table created")
        else:
            print("     ⏭️  Users table already exists")
        
        # 2. Update existing tables
        print("\n🔧 Updating existing tables...")
        
        if table_exists('products'):
            # Add payment fields to products table
            if not column_exists('products', 'payment_type'):
                print("  ➕ Adding payment_type to products...")
                db.session.execute(text("ALTER TABLE products ADD COLUMN payment_type VARCHAR(20) DEFAULT 'external'"))
                print("     ✅ Added payment_type")
            else:
                print("     ⏭️  payment_type already exists")
            
            if not column_exists('products', 'payment_url'):
                print("  ➕ Adding payment_url to products...")
                db.session.execute(text("ALTER TABLE products ADD COLUMN payment_url VARCHAR(300)"))
                print("     ✅ Added payment_url")
            else:
                print("     ⏭️  payment_url already exists")
        
        # Update Raspberry Pi Projects table with resource fields
        if table_exists('raspberry_pi_projects'):
            rpi_columns = [
                ('documentation_json', 'TEXT'),
                ('circuit_diagrams_json', 'TEXT'),
                ('parts_list_json', 'TEXT'),
                ('videos_json', 'TEXT')
            ]
            
            for col_name, col_type in rpi_columns:
                if not column_exists('raspberry_pi_projects', col_name):
                    print(f"  ➕ Adding {col_name} to raspberry_pi_projects...")
                    db.session.execute(text(f"ALTER TABLE raspberry_pi_projects ADD COLUMN {col_name} {col_type}"))
                    print(f"     ✅ Added {col_name}")
                else:
                    print(f"     ⏭️  {col_name} already exists")
        
        # 3. Remove deprecated tables
        print("\n🗑️  Removing deprecated tables...")
        
        if table_exists('about'):
            print("  ❌ Dropping about table (use owner_profile instead)...")
            db.session.execute(text('DROP TABLE about'))
            print("     ✅ About table removed")
        else:
            print("     ⏭️  About table doesn't exist")
        
        if table_exists('contact'):
            print("  ❌ Dropping contact table (use owner_profile instead)...")
            db.session.execute(text('DROP TABLE contact'))
            print("     ✅ Contact table removed")
        else:
            print("     ⏭️  Contact table doesn't exist")
        
        # Commit all changes
        db.session.commit()
        
        print("\n✅ Migration completed successfully!")
        print("\n📊 Current tables:")
        inspector = inspect(db.engine)
        for table in inspector.get_table_names():
            print(f"   - {table}")

def create_default_admin():
    """Create default admin user if none exists"""
    with app.app_context():
        if User.query.count() == 0:
            print("\n👤 Creating default admin user...")
            admin = User(
                username='admin',
                email='admin@example.com',
                full_name='Administrator',
                is_superuser=True
            )
            # Default password: change this immediately after first login!
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
        else:
            print("⏭️  Admin users already exist")

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration Tool")
    print("=" * 60)
    
    try:
        migrate()
        create_default_admin()
        
        print("\n" + "=" * 60)
        print("🎉 All done! Your database is up to date.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("   Database has been rolled back.")
        import traceback
        traceback.print_exc()
