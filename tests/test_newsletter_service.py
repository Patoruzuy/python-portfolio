"""
Tests for newsletter service layer.
"""
import pytest
from datetime import datetime, timezone
from services.newsletter_service import NewsletterService, newsletter_service
from models import Newsletter, db


@pytest.fixture
def service():
    """Get newsletter service instance."""
    return NewsletterService()


class TestNewsletterStats:
    """Test newsletter statistics."""
    
    def test_get_stats_returns_dict(self, database, service):
        """Should return dictionary with counts."""
        stats = service.get_stats()
        
        assert isinstance(stats, dict)
        assert 'total_subscribers' in stats
        assert 'unconfirmed' in stats
        assert 'unsubscribed' in stats
    
    def test_get_stats_counts_active_confirmed(self, database, service):
        """Should count active confirmed subscribers."""
        # Create confirmed subscribers
        sub1 = Newsletter(email='user1@test.com', confirmed=True, active=True)
        sub2 = Newsletter(email='user2@test.com', confirmed=True, active=True)
        db.session.add_all([sub1, sub2])
        db.session.commit()
        
        stats = service.get_stats()
        assert stats['total_subscribers'] == 2
    
    def test_get_stats_counts_unconfirmed(self, database, service):
        """Should count active unconfirmed subscribers."""
        sub = Newsletter(email='unconfirmed@test.com', confirmed=False, active=True)
        db.session.add(sub)
        db.session.commit()
        
        stats = service.get_stats()
        assert stats['unconfirmed'] == 1
    
    def test_get_stats_counts_unsubscribed(self, database, service):
        """Should count inactive subscribers."""
        sub = Newsletter(email='inactive@test.com', active=False)
        db.session.add(sub)
        db.session.commit()
        
        stats = service.get_stats()
        assert stats['unsubscribed'] == 1


class TestGetAllSubscribers:
    """Test retrieving all subscribers."""
    
    def test_get_all_subscribers_returns_list(self, database, service):
        """Should return list of subscribers."""
        result = service.get_all_subscribers()
        assert isinstance(result, list)
    
    def test_get_all_subscribers_active_only(self, database, service):
        """Should return only active subscribers by default."""
        active = Newsletter(email='active@test.com', active=True)
        inactive = Newsletter(email='inactive@test.com', active=False)
        db.session.add_all([active, inactive])
        db.session.commit()
        
        result = service.get_all_subscribers(active_only=True)
        assert len(result) == 1
        assert result[0].email == 'active@test.com'
    
    def test_get_all_subscribers_include_inactive(self, database, service):
        """Should return all subscribers when active_only=False."""
        active = Newsletter(email='active@test.com', active=True)
        inactive = Newsletter(email='inactive@test.com', active=False)
        db.session.add_all([active, inactive])
        db.session.commit()
        
        result = service.get_all_subscribers(active_only=False)
        assert len(result) == 2


class TestGetByEmail:
    """Test retrieving subscription by email."""
    
    def test_get_by_email_returns_subscriber(self, database, service):
        """Should return subscriber by email."""
        sub = Newsletter(email='test@example.com')
        db.session.add(sub)
        db.session.commit()
        
        result = service.get_by_email('test@example.com')
        assert result is not None
        assert result.email == 'test@example.com'
    
    def test_get_by_email_returns_none_not_found(self, database, service):
        """Should return None if email not found."""
        result = service.get_by_email('nonexistent@example.com')
        assert result is None


class TestSubscribe:
    """Test newsletter subscription."""
    
    def test_subscribe_success(self, database, service):
        """Should create new subscription."""
        success, message, subscription = service.subscribe('new@test.com', 'New User')
        
        assert success is True
        assert 'Welcome!' in message
        assert subscription is not None
        assert subscription.email == 'new@test.com'
        assert subscription.name == 'New User'
        assert subscription.confirmation_token is not None
    
    def test_subscribe_without_name(self, database, service):
        """Should allow subscription without name."""
        success, message, subscription = service.subscribe('noname@test.com')
        
        assert success is True
        assert subscription.name is None
    
    def test_subscribe_invalid_email(self, database, service):
        """Should reject invalid email."""
        success, message, subscription = service.subscribe('invalid-email')
        
        assert success is False
        assert 'valid email' in message.lower()
        assert subscription is None
    
    def test_subscribe_empty_email(self, database, service):
        """Should reject empty email."""
        success, message, subscription = service.subscribe('')
        
        assert success is False
        assert subscription is None
    
    def test_subscribe_already_active(self, database, service):
        """Should reject duplicate active subscription."""
        existing = Newsletter(email='existing@test.com', active=True)
        db.session.add(existing)
        db.session.commit()
        
        success, message, subscription = service.subscribe('existing@test.com')
        
        assert success is False
        assert 'already subscribed' in message.lower()
    
    def test_subscribe_reactivates_inactive(self, database, service):
        """Should reactivate inactive subscription."""
        inactive = Newsletter(
            email='inactive@test.com',
            active=False,
            unsubscribed_at=datetime.now(timezone.utc)
        )
        db.session.add(inactive)
        db.session.commit()
        
        success, message, subscription = service.subscribe('inactive@test.com')
        
        assert success is True
        assert 'reactivated' in message.lower()
        assert subscription.active is True
        assert subscription.unsubscribed_at is None
    
    def test_subscribe_generates_token(self, database, service):
        """Should generate confirmation token."""
        success, message, subscription = service.subscribe('token@test.com')
        
        assert subscription.confirmation_token is not None
        assert len(subscription.confirmation_token) > 20


class TestConfirmSubscription:
    """Test subscription confirmation."""
    
    def test_confirm_subscription_success(self, database, service):
        """Should confirm subscription with valid token."""
        sub = Newsletter(
            email='confirm@test.com',
            confirmed=False,
            confirmation_token='valid-token-123'
        )
        db.session.add(sub)
        db.session.commit()
        
        success, message = service.confirm_subscription('valid-token-123')
        
        assert success is True
        assert 'confirmed' in message.lower()
        
        # Verify subscription is confirmed
        sub = Newsletter.query.filter_by(email='confirm@test.com').first()
        assert sub.confirmed is True
    
    def test_confirm_subscription_invalid_token(self, database, service):
        """Should reject invalid token."""
        success, message = service.confirm_subscription('invalid-token')
        
        assert success is False
        assert 'invalid' in message.lower()
    
    def test_confirm_subscription_already_confirmed(self, database, service):
        """Should handle already confirmed subscription."""
        sub = Newsletter(
            email='already@test.com',
            confirmed=True,
            confirmation_token='token-123'
        )
        db.session.add(sub)
        db.session.commit()
        
        success, message = service.confirm_subscription('token-123')
        
        assert success is True
        assert 'already confirmed' in message.lower()


class TestUnsubscribe:
    """Test newsletter unsubscription."""
    
    def test_unsubscribe_success(self, database, service):
        """Should unsubscribe with valid token."""
        sub = Newsletter(
            email='unsub@test.com',
            active=True,
            confirmation_token='unsub-token-123'
        )
        db.session.add(sub)
        db.session.commit()
        
        success, message = service.unsubscribe('unsub-token-123')
        
        assert success is True
        assert 'unsubscribed' in message.lower()
        
        # Verify subscription is inactive
        sub = Newsletter.query.filter_by(email='unsub@test.com').first()
        assert sub.active is False
        assert sub.unsubscribed_at is not None
    
    def test_unsubscribe_invalid_token(self, database, service):
        """Should reject invalid token."""
        success, message = service.unsubscribe('invalid-token')
        
        assert success is False
        assert 'invalid' in message.lower()
    
    def test_unsubscribe_already_unsubscribed(self, database, service):
        """Should handle already unsubscribed."""
        sub = Newsletter(
            email='already-unsub@test.com',
            active=False,
            confirmation_token='token-456'
        )
        db.session.add(sub)
        db.session.commit()
        
        success, message = service.unsubscribe('token-456')
        
        assert success is True
        assert 'already unsubscribed' in message.lower()


class TestDeleteSubscriber:
    """Test subscriber deletion."""
    
    def test_delete_subscriber_success(self, database, service):
        """Should delete subscriber by ID."""
        sub = Newsletter(email='delete@test.com')
        db.session.add(sub)
        db.session.commit()
        
        subscriber_id = sub.id
        result = service.delete_subscriber(subscriber_id)
        
        assert result is True
        assert Newsletter.query.get(subscriber_id) is None
    
    def test_delete_subscriber_not_found(self, database, service):
        """Should return False if subscriber not found."""
        result = service.delete_subscriber(99999)
        assert result is False


class TestGlobalInstance:
    """Test global newsletter_service instance."""
    
    def test_global_instance_exists(self):
        """Should have global newsletter_service instance."""
        assert newsletter_service is not None
        assert isinstance(newsletter_service, NewsletterService)
