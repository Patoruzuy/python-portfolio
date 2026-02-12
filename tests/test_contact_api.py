"""
Simple test to verify the async email endpoint works.
This tests the API endpoint directly without requiring Redis/Celery worker.
"""
import requests
import json

def test_contact_api():
    """Test the contact API endpoint"""
    print("=" * 60)
    print("Testing Contact API Endpoint")
    print("=" * 60)
    
    # Test data
    contact_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'subject': 'Test Contact Form',
        'message': 'This is a test message to verify the contact API endpoint.',
        'projectType': 'Testing'
    }
    
    print("\n📧 Sending contact form data...")
    print(f"   Name: {contact_data['name']}")
    print(f"   Email: {contact_data['email']}")
    print(f"   Subject: {contact_data['subject']}")
    
    try:
        # Send POST request to contact API
        url = 'http://localhost:3000/api/contact'
        headers = {'Content-Type': 'application/json'}
        
        # First, get the CSRF token from the homepage
        print(f"\n🔐 Getting CSRF token...")
        session = requests.Session()
        home_response = session.get('http://localhost:3000/')
        
        # Try to extract CSRF token from meta tag
        import re
        csrf_match = re.search(r'<meta name="csrf-token" content="([^"]+)"', home_response.text)
        
        if csrf_match:
            csrf_token = csrf_match.group(1)
            headers['X-CSRFToken'] = csrf_token
            print(f"   CSRF Token: {csrf_token[:20]}...")
        else:
            print(f"   ⚠️  No CSRF token found (proceeding anyway)")
        
        print(f"\n⏳ Sending POST request to {url}...")
        response = session.post(url, json=contact_data, headers=headers, timeout=10)
        
        print(f"\n✅ Response received!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.3f} seconds")
        
        # Parse response
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Response Data:")
            print(f"   Success: {data.get('success')}")
            print(f"   Message: {data.get('message')}")
            if 'task_id' in data:
                print(f"   Task ID: {data.get('task_id')}")
                print("\n💡 The email is being processed asynchronously!")
                print("   Check Celery worker logs to see the task execution.")
        else:
            print(f"\n❌ Request failed:")
            print(f"   {response.text}")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error!")
        print(f"   Is Flask running on http://localhost:3000?")
        print(f"   Start it with: python app.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 60)
    
    # Show what happens without Redis
    print("\n📝 Note about Celery/Redis:")
    print("   - If Redis is NOT running: API will still respond quickly")
    print("     but you'll see connection errors in Flask logs")
    print("   - If Redis IS running + Worker: Email will be sent async")
    print("\n   To install Redis (Windows):")
    print("     choco install redis-64")
    print("     Or use WSL2: sudo apt install redis-server")
    print("\n   To start Celery worker:")
    print("     celery -A tasks.email_tasks worker --loglevel=info --pool=solo")
    print("=" * 60)

if __name__ == '__main__':
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("❌ requests library not installed")
        print("   Install with: pip install requests")
        exit(1)
    
    test_contact_api()
