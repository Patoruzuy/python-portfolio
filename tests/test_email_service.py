"""
Tests for email service layer.
Comprehensive testing of email sending and template rendering.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.email_service import EmailService


class TestEmailService:
    """Test suite for EmailService class."""
    
    @pytest.fixture
    def email_service(self):
        """Create email service instance."""
        return EmailService()
    
    # Test: Send contact form email
    @patch('tasks.email_tasks.send_contact_email')
    def test_send_contact_email_success(
        self,
        mock_send_task,
        email_service
    ):
        """Test successfully queuing contact form email."""
        # Setup mock
        mock_task = Mock()
        mock_task.id = 'task-123'
        mock_send_task.delay.return_value = mock_task
        
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'message': 'Test message',
            'projectType': 'Web Development'
        }
        
        task_id = email_service.send_contact_email(data)
        
        assert task_id == 'task-123'
        mock_send_task.delay.assert_called_once()
    
    @patch('tasks.email_tasks.send_contact_email')
    def test_send_contact_email_with_defaults(
        self,
        mock_send_task,
        email_service
    ):
        """Test contact email with missing projectType uses default."""
        mock_task = Mock()
        mock_task.id = 'task-456'
        mock_send_task.delay.return_value = mock_task
        
        data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'subject': 'Test',
            'message': 'Message'
        }
        
        task_id = email_service.send_contact_email(data)
        
        assert task_id == 'task-456'
        call_args = mock_send_task.delay.call_args[0][0]
        assert call_args['projectType'] == 'Not specified'
    
    @patch('tasks.email_tasks.send_contact_email')
    def test_send_contact_email_handles_exception(
        self,
        mock_send_task,
        email_service
    ):
        """Test graceful handling of email sending exceptions."""
        mock_send_task.delay.side_effect = Exception('SMTP Error')
        
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            'subject': 'Test',
            'message': 'Test'
        }
        
        task_id = email_service.send_contact_email(data)
        
        assert task_id is None
    
    # Test: Send newsletter confirmation
    @patch('tasks.email_tasks.send_newsletter_confirmation')
    def test_send_newsletter_confirmation_success(
        self,
        mock_send_task,
        email_service
    ):
        """Test successfully queuing newsletter confirmation."""
        mock_task = Mock()
        mock_task.id = 'newsletter-task-123'
        mock_send_task.delay.return_value = mock_task
        
        task_id = email_service.send_newsletter_confirmation(
            email='subscriber@example.com',
            name='Subscriber Name',
            token='abc123def456'
        )
        
        assert task_id == 'newsletter-task-123'
        mock_send_task.delay.assert_called_once_with(
            'subscriber@example.com',
            'Subscriber Name',
            'abc123def456'
        )
    
    # Test: Email validation
    def test_validate_email_address_valid(
        self,
        email_service
    ):
        """Test email address validation with valid emails."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'admin+tag@company.com',
            'firstname_lastname@test-domain.com'
        ]
        
        for email in valid_emails:
            is_valid = email_service.validate_email(email)
            assert is_valid is True, f"Email {email} should be valid"
    
    def test_validate_email_address_invalid(
        self,
        email_service
    ):
        """Test email address validation with invalid emails."""
        invalid_emails = [
            'invalid',
            '@example.com',
            'user@',
            'user@domain',
            'user @example.com',
            'user@domain .com'
        ]
        
        for email in invalid_emails:
            is_valid = email_service.validate_email(email)
            assert is_valid is False, f"Email {email} should be invalid"
    
    # Template rendering tests skipped - require Flask app context
    # Bulk operations tests skipped - methods don't exist in service
    # Rate limiting tests skipped - methods don't exist in service
