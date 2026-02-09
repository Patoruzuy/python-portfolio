"""
Test script for Celery async email functionality.

Usage:
    1. Start Redis: redis-server (or ensure it's running)
    2. Start Celery worker in separate terminal:
       celery -A tasks.email_tasks worker --loglevel=info --pool=solo
    3. Run this script: python test_celery.py
"""
from tasks.email_tasks import send_contact_email
from app import app
import time

def test_async_email():
    """Test async email sending with Celery"""
    print("=" * 60)
    print("Testing Celery Async Email Functionality")
    print("=" * 60)
    
    # Test contact form data
    contact_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'subject': 'Test Async Email',
        'message': 'This is a test message to verify Celery async email functionality is working correctly.',
        'projectType': 'Testing'
    }
    
    print("\n📧 Queueing email task...")
    print(f"   From: {contact_data['name']} ({contact_data['email']})")
    print(f"   Subject: {contact_data['subject']}")
    
    try:
        # Queue the task (non-blocking)
        with app.app_context():
            task = send_contact_email.delay(contact_data)
        
        print(f"\n✅ Task queued successfully!")
        print(f"   Task ID: {task.id}")
        print(f"   State: {task.state}")
        
        # Wait for task to complete (for demonstration)
        print("\n⏳ Waiting for task to complete...")
        timeout = 30  # seconds
        start_time = time.time()
        
        while task.state == 'PENDING' and (time.time() - start_time) < timeout:
            time.sleep(1)
            print(".", end="", flush=True)
        
        print()  # New line after dots
        
        # Check final status
        if task.state == 'SUCCESS':
            print(f"\n✅ Email sent successfully!")
            print(f"   Result: {task.result}")
        elif task.state == 'FAILURE':
            print(f"\n❌ Task failed!")
            print(f"   Error: {task.result}")
        else:
            print(f"\n⚠️  Task still processing (State: {task.state})")
            print(f"   Check Celery worker logs for details")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is Redis running? (redis-cli ping)")
        print("  2. Is Celery worker running?")
        print("  3. Are email settings configured in .env?")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_async_email()
