#!/usr/bin/env python3
"""
Test script to demonstrate how to access and display uploaded profile images.
"""

import requests
import json
import webbrowser
import os

# Configuration
BASE_URL = "http://localhost:8000/api/v1/auth"
EMAIL = "profile_test@example.com"
PASSWORD = "TestPass123"

def test_image_display():
    """Test accessing and displaying the uploaded profile image."""
    print("🖼️  Testing Profile Image Display...")
    
    # Step 1: Login
    session = requests.Session()
    response = session.post(f"{BASE_URL}/login", json={
        "email": EMAIL,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print("❌ Login failed")
        return
    
    print("✅ Login successful")
    
    # Step 2: Get user profile to see current image URL
    response = session.get(f"{BASE_URL}/me")
    if response.status_code == 200:
        user_data = response.json()
        image_url = user_data.get("profile_image_url")
        
        if image_url:
            print(f"📸 Current profile image URL: {image_url}")
            
            # Step 3: Test accessing the image
            full_image_url = f"http://localhost:8000{image_url}"
            print(f"🔗 Full image URL: {full_image_url}")
            
            # Test if image is accessible
            img_response = requests.get(full_image_url)
            if img_response.status_code == 200:
                print("✅ Image is accessible!")
                print(f"📊 Image size: {len(img_response.content)} bytes")
                print(f"📋 Content-Type: {img_response.headers.get('content-type')}")
                
                # Save image locally for testing
                filename = f"downloaded_profile_image_{user_data['id']}.jpg"
                with open(filename, "wb") as f:
                    f.write(img_response.content)
                print(f"💾 Image saved as: {filename}")
                
                # Try to open in browser
                try:
                    webbrowser.open(full_image_url)
                    print("🌐 Opened image in browser")
                except:
                    print("⚠️  Could not open browser automatically")
                    
            else:
                print(f"❌ Image not accessible: {img_response.status_code}")
        else:
            print("❌ No profile image found")
    else:
        print("❌ Failed to get user profile")

if __name__ == "__main__":
    test_image_display() 