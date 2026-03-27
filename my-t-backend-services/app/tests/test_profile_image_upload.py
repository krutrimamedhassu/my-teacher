#!/usr/bin/env python3
"""
Test script for profile image upload functionality.
This script tests the new profile image upload endpoint.
"""

import requests
import json
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1/auth"
TEST_EMAIL = "profile_test@example.com"
TEST_PASSWORD = "TestPass123"
TEST_IMAGE_PATH = "../../test_image.jpg"

def create_test_image():
    """Create a simple test image if it doesn't exist."""
    if not os.path.exists(TEST_IMAGE_PATH):
        # Create a simple 1x1 pixel JPEG image
        from PIL import Image
        img = Image.new('RGB', (1, 1), color='red')
        img.save(TEST_IMAGE_PATH, 'JPEG')
        print(f"✅ Created test image: {TEST_IMAGE_PATH}")

def register_test_user():
    """Register a test user if it doesn't exist."""
    print("🔐 Registering test user...")
    
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": "profile_test_user",
        "full_name": "Profile Test User"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=register_data)
        if response.status_code == 201:
            print("✅ Test user registered successfully")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ Test user already exists")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return False

def test_profile_image_upload():
    """Test the profile image upload endpoint."""
    print("\n🧪 Testing Profile Image Upload...")
    
    # Step 1: Login to get cookies
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        response = session.post(f"{BASE_URL}/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        login_response = response.json()
        print(f"🔍 Debug - Full login response: {json.dumps(login_response, indent=2)}")
        
        # Check if we have cookies
        cookies = session.cookies
        if not cookies:
            print("❌ No cookies received")
            return None
        
        print("✅ Login successful")
        print(f"🍪 Cookies: {dict(cookies)}")
        
        # Step 2: Upload profile image using session (which includes cookies)
        with open(TEST_IMAGE_PATH, "rb") as f:
            files = {"file": (TEST_IMAGE_PATH, f, "image/jpeg")}
            response = session.post(
                f"{BASE_URL}/profile-image",
                files=files
            )
        
        print(f"📤 Upload Response Status: {response.status_code}")
        print(f"📤 Upload Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Profile image upload successful!")
            
            # Step 3: Get user profile to verify image URL
            response = session.get(f"{BASE_URL}/me")
            if response.status_code == 200:
                user_data = response.json()
                print(f"👤 User Profile: {json.dumps(user_data, indent=2)}")
                print("✅ Profile image URL updated successfully!")
            else:
                print(f"❌ Failed to get user profile: {response.status_code}")
        else:
            print("❌ Profile image upload failed!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    create_test_image()
    if register_test_user():
        test_profile_image_upload()
    else:
        print("❌ Cannot proceed without test user") 