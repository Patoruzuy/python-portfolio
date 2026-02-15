"""
Test script for GDPR compliance features
Run this with: python test_gdpr_features.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_cookie_consent_endpoint():
    """Test /api/cookie-consent endpoint"""
    print("\n🧪 Testing Cookie Consent Logging...")
    
    data = {
        'consent_type': 'accepted',
        'categories': ['necessary', 'analytics']
    }
    
    response = requests.post(
        f"{BASE_URL}/api/cookie-consent",
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("✅ Cookie consent logged successfully")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")

def test_my_data_page():
    """Test /my-data page loads"""
    print("\n🧪 Testing My Data Page...")
    
    response = requests.get(f"{BASE_URL}/my-data")
    
    if response.status_code == 200:
        print("✅ My Data page loaded successfully")
        print(f"   Content length: {len(response.text)} bytes")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_data_download():
    """Test /api/my-data/download endpoint"""
    print("\n🧪 Testing Data Download...")
    
    # First, set a cookie to have some data
    session = requests.Session()
    session.get(BASE_URL)
    
    response = session.get(f"{BASE_URL}/api/my-data/download")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Data download successful")
        print(f"   Page views: {len(data.get('page_views', []))}")
        print(f"   Events: {len(data.get('events', []))}")
        print(f"   Consent history: {len(data.get('consent_history', []))}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")

def test_dnt_header():
    """Test DNT header respect"""
    print("\n🧪 Testing DNT Header...")
    
    # Visit with DNT=1
    response = requests.get(
        BASE_URL,
        headers={'DNT': '1'},
        cookies={'cookie_consent': 'accepted'}
    )
    
    if response.status_code == 200:
        print("✅ Page loaded with DNT=1")
        print("   (Check logs to verify no tracking occurred)")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_granular_consent():
    """Test granular consent categories"""
    print("\n🧪 Testing Granular Consent...")
    
    # Test partial consent (only analytics)
    data = {
        'consent_type': 'partial',
        'categories': ['necessary', 'analytics']
    }
    
    response = requests.post(
        f"{BASE_URL}/api/cookie-consent",
        json=data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        print("✅ Partial consent logged successfully")
        print(f"   Categories: {data['categories']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    print("=" * 60)
    print("GDPR Compliance Features Test Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now()}")
    
    try:
        test_cookie_consent_endpoint()
        test_my_data_page()
        test_data_download()
        test_dnt_header()
        test_granular_consent()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print("\nNote: Make sure Flask app is running on port 5000")
        print("Start with: flask run")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to Flask app")
        print("Make sure the app is running: flask run")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
