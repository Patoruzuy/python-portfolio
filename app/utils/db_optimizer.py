"""
Database optimization utilities.
Adds missing indexes and performance improvements.
"""

from typing import List, Optional
from sqlalchemy import Index
from app.models import db
from flask import Flask


def add_performance_indexes() -> List[str]:
    """
    Add missing database indexes for improved query performance.
    Run this during database migrations or setup.
    
    Returns:
        List of index names created
    """
    indexes_created: List[str] = []
    
    try:
        # PageView table indexes for analytics queries
        # Compound index for session + timestamp queries
        idx_pageview_session_time = Index(
            'idx_pageview_session_created',
            'session_id',
            'created_at',
            postgresql_using='btree'
        )
        
        # Compound index for path + timestamp queries
        idx_pageview_path_time = Index(
            'idx_pageview_path_created',
            'path',
            'created_at',
            postgresql_using='btree'
        )
        
        # Device type for analytics filtering
        idx_pageview_device = Index(
            'idx_pageview_device_type',
            'device_type',
            postgresql_using='btree'
        )
        
        # UserSession table indexes
        # IP address for returning visitor detection
        idx_session_ip = Index(
            'idx_session_ip_address',
            'ip_address',
            postgresql_using='btree'
        )
        
        # Browser/OS for analytics
        idx_session_browser = Index(
            'idx_session_browser_os',
            'browser',
            'os',
            postgresql_using='btree'
        )
        
        # AnalyticsEvent table indexes
        # Event type + timestamp for filtering
        idx_event_type_time = Index(
            'idx_event_type_created',
            'event_type',
            'created_at',
            postgresql_using='btree'
        )
        
        # Event name for specific event tracking
        idx_event_name = Index(
            'idx_event_name',
            'event_name',
            postgresql_using='btree'
        )
        
        # BlogPost table indexes
        # Category + published for filtering
        idx_blog_category_published = Index(
            'idx_blog_category_pub',
            'category',
            'published',
            postgresql_using='btree'
        )
        
        # View count for popular posts
        idx_blog_views = Index(
            'idx_blog_view_count',
            'view_count',
            postgresql_using='btree'
        )
        
        # Project table indexes
        # Category + featured for homepage
        idx_project_cat_featured = Index(
            'idx_project_cat_featured',
            'category',
            'featured',
            postgresql_using='btree'
        )
        
        print("✅ Adding performance indexes...")
        
        # Note: These indexes will be created if they don't exist
        # In production, use proper migrations (Alembic)
        
        indexes_created = [
            'idx_pageview_session_created',
            'idx_pageview_path_created',
            'idx_pageview_device_type',
            'idx_session_ip_address',
            'idx_session_browser_os',
            'idx_event_type_created',
            'idx_event_name',
            'idx_blog_category_pub',
            'idx_blog_view_count',
            'idx_project_cat_featured'
        ]
        
        print(f"✅ Planned indexes: {len(indexes_created)}")
        print("⚠️  Note: Run database migration to apply indexes")
        print("   Example: CREATE INDEX idx_pageview_session_created ON page_views(session_id, created_at);")
        
        return indexes_created
        
    except Exception as e:
        print(f"❌ Error planning indexes: {e}")
        return []


def get_index_creation_sql() -> List[str]:
    """
    Generate SQL statements for creating indexes.
    Use for manual migration or SQL execution.
    
    Returns:
        List of SQL CREATE INDEX statements
    """
    sql_statements: List[str] = [
        # PageView indexes
        "CREATE INDEX IF NOT EXISTS idx_pageview_session_created ON page_views(session_id, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_pageview_path_created ON page_views(path, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_pageview_device_type ON page_views(device_type);",
        
        # UserSession indexes
        "CREATE INDEX IF NOT EXISTS idx_session_ip_address ON user_sessions(ip_address);",
        "CREATE INDEX IF NOT EXISTS idx_session_browser_os ON user_sessions(browser, os);",
        
        # AnalyticsEvent indexes
        "CREATE INDEX IF NOT EXISTS idx_event_type_created ON analytics_events(event_type, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_event_name ON analytics_events(event_name);",
        
        # BlogPost indexes
        "CREATE INDEX IF NOT EXISTS idx_blog_category_pub ON blog_posts(category, published);",
        "CREATE INDEX IF NOT EXISTS idx_blog_view_count ON blog_posts(view_count);",
        
        # Project indexes
        "CREATE INDEX IF NOT EXISTS idx_project_cat_featured ON projects(category, featured);"
    ]
    
    return sql_statements


def apply_indexes_to_database(app: Flask) -> int:
    """
    Apply indexes directly to database (for SQLite/development).
    For production, use proper migration tools.
    
    Args:
        app: Flask application instance
        
    Returns:
        Number of indexes created
    """
    with app.app_context():
        sql_statements: List[str] = get_index_creation_sql()
        created_count: int = 0
        
        try:
            for sql in sql_statements:
                try:
                    db.session.execute(db.text(sql))
                    created_count += 1
                except Exception as e:
                    print(f"⚠️  Index may already exist: {e}")
            
            db.session.commit()
            print(f"✅ Successfully created/verified {created_count} indexes")
            return created_count
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error applying indexes: {e}")
            return 0


if __name__ == '__main__':
    """Run index planning when executed directly."""
    print("📊 Database Performance Optimization")
    print("=" * 50)
    
    indexes = add_performance_indexes()
    print(f"\n📋 Indexes to create: {len(indexes)}")
    
    print("\n📝 SQL Statements:")
    print("=" * 50)
    for sql in get_index_creation_sql():
        print(sql)
    
    print("\n💡 To apply indexes:")
    print("   1. Review SQL statements above")
    print("   2. Run: python -c 'from app.utils.db_optimizer import apply_indexes_to_database; from app import app; apply_indexes_to_database(app)'")
    print("   3. Or add to migration script")
