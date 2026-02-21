"""
Newsletter service layer.
Handles newsletter subscription, confirmation, and management.
"""
from app.models import db, Newsletter
from app.services import BaseService, cache_result, invalidate_cache_pattern
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
import secrets


class NewsletterService(BaseService):
    """Service for newsletter operations."""
    
    @cache_result(timeout=300, key_prefix='newsletter:stats')
    def get_stats(self) -> Dict[str, int]:
        """
        Get newsletter statistics.
        
        Returns:
            Dictionary with subscriber counts
        """
        return {
            'total_subscribers': Newsletter.query.filter_by(
                active=True, confirmed=True
            ).count(),
            'unconfirmed': Newsletter.query.filter_by(
                active=True, confirmed=False
            ).count(),
            'unsubscribed': Newsletter.query.filter_by(active=False).count()
        }
    
    def get_all_subscribers(self, active_only: bool = True) -> list[Newsletter]:
        """
        Get all newsletter subscribers.
        
        Args:
            active_only: Whether to return only active subscribers
            
        Returns:
            List of Newsletter subscribers
        """
        query = Newsletter.query
        if active_only:
            query = query.filter_by(active=True)
        return query.all()
    
    def get_by_email(self, email: str) -> Optional[Newsletter]:
        """
        Get newsletter subscription by email.
        
        Args:
            email: Subscriber email
            
        Returns:
            Newsletter subscription or None
        """
        return Newsletter.query.filter_by(email=email).first()
    
    def subscribe(self, email: str, name: Optional[str] = None) -> Tuple[bool, str, Optional[Newsletter]]:
        """
        Subscribe to newsletter.
        
        Args:
            email: Subscriber email
            name: Subscriber name (optional)
            
        Returns:
            Tuple of (success, message, subscription)
        """
        # Validate email
        if not email or '@' not in email:
            return False, 'Please provide a valid email address.', None
        
        # Check if already subscribed
        existing = self.get_by_email(email)
        if existing:
            if existing.active:
                return False, 'This email is already subscribed to our newsletter.', None
            else:
                # Reactivate subscription
                existing.active = True
                existing.unsubscribed_at = None
                db.session.commit()
                self._invalidate_cache()
                return True, 'Welcome back! Your subscription has been reactivated.', existing
        
        # Create new subscription
        subscription = Newsletter(
            email=email,
            name=name if name else None,
            confirmation_token=secrets.token_urlsafe(32)
        )
        
        db.session.add(subscription)
        db.session.commit()
        self._invalidate_cache()
        
        return True, f'Welcome! Check your inbox at {email} to confirm your subscription.', subscription
    
    def confirm_subscription(self, token: str) -> Tuple[bool, str]:
        """
        Confirm newsletter subscription using token.
        
        Args:
            token: Confirmation token
            
        Returns:
            Tuple of (success, message)
        """
        subscription = Newsletter.query.filter_by(
            confirmation_token=token
        ).first()
        
        if not subscription:
            return False, 'Invalid confirmation link.'
        
        if subscription.confirmed:
            return True, 'Your subscription is already confirmed!'
        
        subscription.confirmed = True
        db.session.commit()
        self._invalidate_cache()
        
        return True, 'Subscription confirmed! You will now receive our newsletter.'
    
    def unsubscribe(self, token: str) -> Tuple[bool, str]:
        """
        Unsubscribe from newsletter using token.
        
        Args:
            token: Confirmation token
            
        Returns:
            Tuple of (success, message)
        """
        subscription = Newsletter.query.filter_by(
            confirmation_token=token
        ).first()
        
        if not subscription:
            return False, 'Invalid unsubscribe link.'
        
        if not subscription.active:
            return True, 'You are already unsubscribed.'
        
        subscription.active = False
        subscription.unsubscribed_at = datetime.now(timezone.utc)
        db.session.commit()
        self._invalidate_cache()
        
        return True, 'You have been unsubscribed from the newsletter.'
    
    def delete_subscriber(self, subscriber_id: int) -> bool:
        """
        Delete newsletter subscriber (admin function).
        
        Args:
            subscriber_id: Subscriber ID
            
        Returns:
            True if deleted, False otherwise
        """
        subscriber = Newsletter.query.get(subscriber_id)
        if not subscriber:
            return False
        
        db.session.delete(subscriber)
        db.session.commit()
        self._invalidate_cache()
        
        return True
    
    def _invalidate_cache(self) -> None:
        """Invalidate newsletter cache."""
        invalidate_cache_pattern('newsletter:stats')


# Global instance
newsletter_service = NewsletterService()
