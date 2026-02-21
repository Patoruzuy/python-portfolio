"""
Tests for database optimizer - index creation and SQL generation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.utils.db_optimizer import (
    add_performance_indexes,
    get_index_creation_sql,
    apply_indexes_to_database
)


class TestIndexPlanning:
    """Test index planning and recommendation."""
    
    def test_add_performance_indexes_returns_list(self):
        """Should return list of planned index names."""
        indexes = add_performance_indexes()
        assert isinstance(indexes, list)
        assert len(indexes) > 0
    
    def test_add_performance_indexes_includes_pageview_indexes(self):
        """Should plan PageView table indexes."""
        indexes = add_performance_indexes()
        assert 'idx_pageview_session_created' in indexes
        assert 'idx_pageview_path_created' in indexes
        assert 'idx_pageview_device_type' in indexes
    
    def test_add_performance_indexes_includes_session_indexes(self):
        """Should plan UserSession table indexes."""
        indexes = add_performance_indexes()
        assert 'idx_session_ip_address' in indexes
        assert 'idx_session_browser_os' in indexes
    
    def test_add_performance_indexes_includes_event_indexes(self):
        """Should plan AnalyticsEvent table indexes."""
        indexes = add_performance_indexes()
        assert 'idx_event_type_created' in indexes
        assert 'idx_event_name' in indexes
    
    def test_add_performance_indexes_includes_blog_indexes(self):
        """Should plan BlogPost table indexes."""
        indexes = add_performance_indexes()
        assert 'idx_blog_category_pub' in indexes
        assert 'idx_blog_view_count' in indexes
    
    def test_add_performance_indexes_includes_project_indexes(self):
        """Should plan Project table indexes."""
        indexes = add_performance_indexes()
        assert 'idx_project_cat_featured' in indexes
    
    def test_add_performance_indexes_count(self):
        """Should plan correct number of indexes."""
        indexes = add_performance_indexes()
        assert len(indexes) == 10  # Total planned indexes


class TestSQLGeneration:
    """Test SQL statement generation for indexes."""
    
    def test_get_index_creation_sql_returns_list(self):
        """Should return list of SQL statements."""
        sql_statements = get_index_creation_sql()
        assert isinstance(sql_statements, list)
        assert len(sql_statements) > 0
    
    def test_get_index_creation_sql_all_create_index(self):
        """All statements should be CREATE INDEX."""
        sql_statements = get_index_creation_sql()
        for sql in sql_statements:
            assert sql.startswith('CREATE INDEX')
            assert 'IF NOT EXISTS' in sql
    
    def test_get_index_creation_sql_pageview_statements(self):
        """Should include PageView index statements."""
        sql_statements = get_index_creation_sql()
        sql_text = ' '.join(sql_statements)
        
        assert 'idx_pageview_session_created' in sql_text
        assert 'page_views' in sql_text
        assert 'session_id' in sql_text
    
    def test_get_index_creation_sql_session_statements(self):
        """Should include UserSession index statements."""
        sql_statements = get_index_creation_sql()
        sql_text = ' '.join(sql_statements)
        
        assert 'idx_session_ip_address' in sql_text
        assert 'user_sessions' in sql_text
    
    def test_get_index_creation_sql_event_statements(self):
        """Should include AnalyticsEvent index statements."""
        sql_statements = get_index_creation_sql()
        sql_text = ' '.join(sql_statements)
        
        assert 'idx_event_type_created' in sql_text
        assert 'analytics_events' in sql_text
    
    def test_get_index_creation_sql_blog_statements(self):
        """Should include BlogPost index statements."""
        sql_statements = get_index_creation_sql()
        sql_text = ' '.join(sql_statements)
        
        assert 'idx_blog_category_pub' in sql_text
        assert 'blog_posts' in sql_text
    
    def test_get_index_creation_sql_project_statements(self):
        """Should include Project index statements."""
        sql_statements = get_index_creation_sql()
        sql_text = ' '.join(sql_statements)
        
        assert 'idx_project_cat_featured' in sql_text
        assert 'projects' in sql_text
    
    def test_get_index_creation_sql_count(self):
        """Should generate correct number of SQL statements."""
        sql_statements = get_index_creation_sql()
        assert len(sql_statements) == 10


class TestIndexApplication:
    """Test applying indexes to database."""
    
    @patch('app.utils.db_optimizer.db')
    def test_apply_indexes_executes_all_statements(self, mock_db):
        """Should execute all SQL statements."""
        mock_app = Mock()
        mock_app.app_context.return_value.__enter__ = Mock()
        mock_app.app_context.return_value.__exit__ = Mock()
        
        mock_session = Mock()
        mock_db.session = mock_session
        mock_db.text = lambda x: x
        
        count = apply_indexes_to_database(mock_app)
        
        # Should have executed SQL statements
        assert mock_session.execute.called
        assert mock_session.commit.called
        assert count >= 0
    
    @patch('app.utils.db_optimizer.db')
    def test_apply_indexes_handles_existing_indexes(self, mock_db):
        """Should handle indexes that already exist."""
        mock_app = Mock()
        mock_app.app_context.return_value.__enter__ = Mock()
        mock_app.app_context.return_value.__exit__ = Mock()
        
        mock_session = Mock()
        # Simulate index already exists
        mock_session.execute.side_effect = Exception('index already exists')
        mock_db.session = mock_session
        mock_db.text = lambda x: x
        
        count = apply_indexes_to_database(mock_app)
        
        # Should handle gracefully and continue
        assert mock_session.execute.called
        assert count == 0  # No new indexes created
    
    @patch('app.utils.db_optimizer.db')
    def test_apply_indexes_commits_changes(self, mock_db):
        """Should commit changes after creating indexes."""
        mock_app = Mock()
        mock_app.app_context.return_value.__enter__ = Mock()
        mock_app.app_context.return_value.__exit__ = Mock()
        
        mock_session = Mock()
        mock_db.session = mock_session
        mock_db.text = lambda x: x
        
        apply_indexes_to_database(mock_app)
        
        assert mock_session.commit.called
    
    @patch('app.utils.db_optimizer.db')
    def test_apply_indexes_rollback_on_error(self, mock_db):
        """Should rollback on error."""
        mock_app = Mock()
        mock_app.app_context.return_value.__enter__ = Mock()
        mock_app.app_context.return_value.__exit__ = Mock()
        
        mock_session = Mock()
        mock_session.commit.side_effect = Exception('Database error')
        mock_db.session = mock_session
        mock_db.text = lambda x: x
        
        count = apply_indexes_to_database(mock_app)
        
        assert mock_session.rollback.called
        assert count == 0
    
    @patch('app.utils.db_optimizer.db')
    def test_apply_indexes_returns_count(self, mock_db):
        """Should return count of indexes created."""
        mock_app = Mock()
        mock_app.app_context.return_value.__enter__ = Mock()
        mock_app.app_context.return_value.__exit__ = Mock()
        
        mock_session = Mock()
        mock_db.session = mock_session
        mock_db.text = lambda x: x
        
        count = apply_indexes_to_database(mock_app)
        
        assert isinstance(count, int)
        assert count >= 0


class TestIndexOptimizations:
    """Test specific index optimizations."""
    
    def test_pageview_session_index_for_analytics(self):
        """PageView session+time index should optimize analytics queries."""
        sql_statements = get_index_creation_sql()
        session_index = next(s for s in sql_statements if 'idx_pageview_session_created' in s)
        
        assert 'session_id' in session_index
        assert 'created_at' in session_index
        assert 'page_views' in session_index
    
    def test_pageview_path_index_for_popular_pages(self):
        """PageView path+time index should optimize popular pages query."""
        sql_statements = get_index_creation_sql()
        path_index = next(s for s in sql_statements if 'idx_pageview_path_created' in s)
        
        assert 'path' in path_index
        assert 'created_at' in path_index
    
    def test_blog_category_index_for_filtering(self):
        """BlogPost category+published index should optimize filtering."""
        sql_statements = get_index_creation_sql()
        blog_index = next(s for s in sql_statements if 'idx_blog_category_pub' in s)
        
        assert 'category' in blog_index
        assert 'published' in blog_index
    
    def test_event_type_index_for_event_filtering(self):
        """AnalyticsEvent type+time index should optimize event queries."""
        sql_statements = get_index_creation_sql()
        event_index = next(s for s in sql_statements if 'idx_event_type_created' in s)
        
        assert 'event_type' in event_index
        assert 'created_at' in event_index
    
    def test_session_ip_index_for_visitor_tracking(self):
        """UserSession IP index should optimize returning visitor detection."""
        sql_statements = get_index_creation_sql()
        ip_index = next(s for s in sql_statements if 'idx_session_ip_address' in s)
        
        assert 'ip_address' in ip_index
        assert 'user_sessions' in ip_index


class TestSQLSafety:
    """Test SQL generation safety."""
    
    def test_sql_uses_if_not_exists(self):
        """All SQL should use IF NOT EXISTS to be idempotent."""
        sql_statements = get_index_creation_sql()
        for sql in sql_statements:
            assert 'IF NOT EXISTS' in sql
    
    def test_sql_properly_formatted(self):
        """SQL statements should be properly formatted."""
        sql_statements = get_index_creation_sql()
        for sql in sql_statements:
            # Should end with semicolon
            assert sql.endswith(';')
            # Should have ON clause
            assert ' ON ' in sql
            # Should have table and columns in parentheses
            assert '(' in sql and ')' in sql
