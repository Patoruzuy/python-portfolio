"""
Email service layer.
Handles email template rendering and sending via Celery tasks.
"""
from typing import Dict, Any, Optional
from app.services import BaseService


class EmailService(BaseService):
    """Service for email operations."""
    
    def send_contact_email(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Queue contact form email to be sent via Celery.
        
        Args:
            data: Contact form data (name, email, subject, message, projectType)
            
        Returns:
            Task ID or None on error
        """
        try:
            from app.tasks.email_tasks import send_contact_email
            
            task = send_contact_email.delay({
                'name': data.get('name'),
                'email': data.get('email'),
                'subject': data.get('subject'),
                'message': data.get('message'),
                'projectType': data.get('projectType', 'Not specified')
            })
            
            return task.id
        except Exception as e:
            print(f"Error queuing contact email: {e}")
            return None
    
    def send_newsletter_confirmation(
        self,
        email: str,
        name: Optional[str],
        token: str
    ) -> Optional[str]:
        """
        Queue newsletter confirmation email via Celery.
        
        Args:
            email: Subscriber email
            name: Subscriber name
            token: Confirmation token
            
        Returns:
            Task ID or None on error
        """
        try:
            from app.tasks.email_tasks import send_newsletter_confirmation
            
            task = send_newsletter_confirmation.delay(email, name, token)
            return task.id
        except Exception as e:
            print(f"Error queuing newsletter confirmation: {e}")
            return None
    
    def send_password_reset_email(
        self,
        email: str,
        reset_url: str,
        expires_in_minutes: int = 60
    ) -> Optional[str]:
        """
        Send password reset email to admin.
        
        Args:
            email: Admin email
            reset_url: Password reset URL
            expires_in_minutes: Token expiration time
            
        Returns:
            Task ID or None on error
        """
        try:
            from flask_mail import Message
            from flask import current_app
            
            # Check if mail is configured
            mail = current_app.extensions.get('mail')
            if not mail:
                print("Email not configured")
                return None
            
            msg = Message(
                subject='Password Reset Request',
                recipients=[email],
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            # Email body template
            msg.body = f"""
Hello,

You requested a password reset for your admin account.

Please click the following link to reset your password:
{reset_url}

This link will expire in {expires_in_minutes} minutes.

If you did not request this reset, please ignore this email.

Best regards,
Portfolio Admin System
            """.strip()
            
            # Queue email via Celery if available
            try:
                from app.tasks.email_tasks import send_async_email
                task = send_async_email.delay(msg)
                return task.id
            except Exception:
                # Fallback: send synchronously
                mail.send(msg)
                return "sync"
                
        except Exception as e:
            print(f"Error sending password reset email: {e}")
            return None
    
    def render_email_template(
        self,
        template_name: str,
        **context: Any
    ) -> str:
        """
        Render email template with context.
        
        Args:
            template_name: Template file name
            **context: Template context variables
            
        Returns:
            Rendered email HTML
        """
        try:
            from flask import render_template
            return render_template(f'emails/{template_name}', **context)
        except Exception as e:
            print(f"Error rendering email template: {e}")
            return ""
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))


# Global instance
email_service = EmailService()
