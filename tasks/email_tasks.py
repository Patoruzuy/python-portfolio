"""
Celery tasks for async email sending.

To start the Celery worker:
    celery -A celery_config.celery worker --loglevel=info --pool=solo

Note: Use --pool=solo on Windows due to Celery's limitations with multiprocessing on Windows.
"""
from flask import render_template
from flask_mail import Message
from celery_config import celery
from app import app, mail


@celery.task(bind=True, name='tasks.email_tasks.send_contact_email', max_retries=3)
def send_contact_email(self, contact_data):
    """
    Async task to send contact form email.
    
    Args:
        contact_data (dict): Dictionary containing contact form data
            - name (str): Sender's name
            - email (str): Sender's email
            - subject (str): Email subject
            - message (str): Email message body
            - project_type (str, optional): Type of project inquiry
            
    Returns:
        dict: Result status with success/failure information
        
    Raises:
        Exception: If email sending fails after max retries
    """
    try:
        # Extract contact data
        name = contact_data.get('name')
        email = contact_data.get('email')
        subject = contact_data.get('subject')
        message_body = contact_data.get('message')
        project_type = contact_data.get('projectType', 'Not specified')
        
        # Create email message
        msg = Message(
            subject=f"Portfolio Contact: {subject}",
            sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@portfolio.com'),
            recipients=[app.config.get('CONTACT_EMAIL', app.config.get('MAIL_USERNAME'))],
            reply_to=email
        )
        
        # Create HTML body
        msg.html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 10px;">
                        New Contact Form Submission
                    </h2>
                    
                    <div style="margin: 20px 0;">
                        <p style="margin: 10px 0;">
                            <strong>From:</strong> {name} ({email})
                        </p>
                        <p style="margin: 10px 0;">
                            <strong>Subject:</strong> {subject}
                        </p>
                        <p style="margin: 10px 0;">
                            <strong>Project Type:</strong> {project_type}
                        </p>
                    </div>
                    
                    <div style="margin: 20px 0; padding: 15px; background-color: #f9fafb; border-left: 4px solid #6366f1; border-radius: 3px;">
                        <h3 style="margin-top: 0; color: #6366f1;">Message:</h3>
                        <p style="white-space: pre-wrap;">{message_body}</p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
                        <p>This email was sent from your portfolio contact form.</p>
                        <p>Reply directly to this email to respond to {name}.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Create plain text version
        msg.body = f"""
New Contact Form Submission
============================

From: {name} ({email})
Subject: {subject}
Project Type: {project_type}

Message:
--------
{message_body}

---
This email was sent from your portfolio contact form.
Reply directly to this email to respond to {name}.
        """
        
        # Send email
        with app.app_context():
            mail.send(msg)
        
        return {
            'success': True,
            'message': f'Email sent successfully to {name}',
            'task_id': self.request.id
        }
        
    except Exception as exc:
        # Log the error
        print(f"Error sending email: {exc}")
        
        # Retry with exponential backoff (30s, 60s, 120s)
        try:
            raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            # Max retries exceeded, return failure
            return {
                'success': False,
                'error': f'Failed to send email after {self.max_retries} retries: {str(exc)}',
                'task_id': self.request.id
            }


@celery.task(name='tasks.email_tasks.send_newsletter_confirmation')
def send_newsletter_confirmation(email, name, confirmation_token):
    """
    Async task to send newsletter confirmation email.
    
    Args:
        email (str): Subscriber's email address
        name (str): Subscriber's name (optional)
        confirmation_token (str): Unique confirmation token
        
    Returns:
        dict: Result status
    """
    try:
        from datetime import datetime
        
        with app.app_context():
            # Get site configuration
            from models import SiteConfig, OwnerProfile
            site_config = SiteConfig.query.first()
            owner = OwnerProfile.query.first()
            
            site_url = app.config.get('SITE_URL', 'http://localhost:5000')
            confirmation_url = f"{site_url}/newsletter/confirm/{confirmation_token}"
            unsubscribe_url = f"{site_url}/newsletter/unsubscribe/{confirmation_token}"
            
            # Render HTML email from template
            html_body = render_template(
                'emails/newsletter_confirmation.html',
                name=name,
                confirmation_url=confirmation_url,
                unsubscribe_url=unsubscribe_url,
                site_url=site_url,
                owner_name=owner.name if owner else 'Portfolio Owner',
                year=datetime.now().year
            )
            
            # Create plain text version
            text_body = f"""
Welcome{', ' + name if name else ''}!

You're almost there! Click the link below to confirm your email subscription:

{confirmation_url}

If you didn't request this subscription, you can safely ignore this email.

---
This email was sent because you subscribed to the newsletter at {site_url}
© {datetime.now().year} {owner.name if owner else 'Portfolio Owner'}. All rights reserved.
            """.strip()
            
            msg = Message(
                subject='Confirm Your Newsletter Subscription',
                sender=app.config.get('MAIL_DEFAULT_SENDER'),
                recipients=[email]
            )
            
            msg.html = html_body
            msg.body = text_body
            
            mail.send(msg)
        
        return {'success': True, 'email': email}
        
    except Exception as exc:
        print(f"Error sending confirmation to {email}: {exc}")
        return {'success': False, 'email': email, 'error': str(exc)}


@celery.task(name='tasks.email_tasks.send_newsletter')
def send_newsletter(subscriber_email, newsletter_content):
    """
    Async task to send newsletter emails.
    
    Args:
        subscriber_email (str): Subscriber's email address
        newsletter_content (dict): Newsletter content with:
            - title: Email subject
            - subtitle: Optional subtitle
            - content: HTML content body
            - featured_image: Optional image URL
            - cta_text: Optional call-to-action button text
            - cta_url: Optional call-to-action URL
        
    Returns:
        dict: Result status
    """
    try:
        from datetime import datetime
        
        with app.app_context():
            # Get site configuration
            from models import SiteConfig, OwnerProfile, Newsletter
            site_config = SiteConfig.query.first()
            owner = OwnerProfile.query.first()
            subscriber = Newsletter.query.filter_by(email=subscriber_email).first()
            
            site_url = app.config.get('SITE_URL', 'http://localhost:5000')
            unsubscribe_url = f"{site_url}/newsletter/unsubscribe/{subscriber.confirmation_token if subscriber else 'unknown'}"
            
            # Render HTML email from template
            html_body = render_template(
                'emails/newsletter_template.html',
                title=newsletter_content.get('title', 'Newsletter'),
                subtitle=newsletter_content.get('subtitle'),
                content=newsletter_content.get('content', ''),
                featured_image=newsletter_content.get('featured_image'),
                cta_text=newsletter_content.get('cta_text'),
                cta_url=newsletter_content.get('cta_url'),
                site_url=site_url,
                unsubscribe_url=unsubscribe_url,
                owner_name=owner.name if owner else 'Portfolio Owner',
                year=datetime.now().year
            )
            
            # Create plain text version
            text_body = newsletter_content.get('text_body', '')
            if not text_body:
                # Simple conversion from HTML content
                import re
                text_body = re.sub('<[^<]+?>', '', newsletter_content.get('content', ''))
            
            msg = Message(
                subject=newsletter_content.get('title', 'Newsletter'),
                sender=app.config.get('MAIL_DEFAULT_SENDER'),
                recipients=[subscriber_email]
            )
            
            msg.html = html_body
            msg.body = text_body
            
            mail.send(msg)
        
        return {'success': True, 'email': subscriber_email}
        
    except Exception as exc:
        print(f"Error sending newsletter to {subscriber_email}: {exc}")
        return {'success': False, 'email': subscriber_email, 'error': str(exc)}

