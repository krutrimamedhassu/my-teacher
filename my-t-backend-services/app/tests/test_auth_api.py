#!/usr/bin/env python3
"""
Test script for the Authentication API

This script demonstrates how to use the authentication endpoints:
- User registration
- User login
- Profile updates
- Password updates
- Email updates

Make sure to:
1. Set up your MongoDB connection string in your environment
2. Install the required dependencies: pip install -r requirements.txt
3. Start the FastAPI server: python -m app.main
"""

import requests
import json
from typing import Dict, Any

# API base URL - adjust if your server runs on a different port
BASE_URL = "http://localhost:8000/api/v1/auth"

def print_response(response: requests.Response, title: str):
    """Print formatted API response."""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print(f"{'='*50}")

def test_user_registration():
    """Test user registration endpoint."""
    print("\n🧪 Testing User Registration...")
    
    user_data = {
        "email": "testuser@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "SecurePass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=user_data)
        print_response(response, "User Registration")
        return response.json() if response.status_code == 201 else None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
        return None

def test_user_login():
    """Test user login endpoint."""
    print("\n🧪 Testing User Login...")
    
    login_data = {
        "email": "testuser@example.com",
        "password": "SecurePass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print_response(response, "User Login")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
        return None

def test_get_current_user(access_token: str):
    """Test getting current user information."""
    print("\n🧪 Testing Get Current User...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        print_response(response, "Get Current User")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
        return None

def test_update_profile(access_token: str):
    """Test updating user profile."""
    print("\n🧪 Testing Update Profile...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    update_data = {
        "full_name": "Updated Test User",
        "username": "updatedtestuser"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/profile", json=update_data, headers=headers)
        print_response(response, "Update Profile")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
        return None

def test_update_password(access_token: str):
    """Test updating user password."""
    print("\n🧪 Testing Update Password...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    password_data = {
        "current_password": "SecurePass123",
        "new_password": "NewSecurePass456"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/password", json=password_data, headers=headers)
        print_response(response, "Update Password")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
        return None

def test_update_email(access_token: str):
    """Test updating user email."""
    print("\n🧪 Testing Update Email...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    email_data = {
        "current_password": "NewSecurePass456",
        "new_email": "updatedtestuser@example.com"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/email", json=email_data, headers=headers)
        print_response(response, "Update Email")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
        return None

def test_refresh_token(access_token: str):
    """Test refreshing access token."""
    print("\n🧪 Testing Refresh Token...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/refresh", headers=headers)
        print_response(response, "Refresh Token")
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the server is running on http://localhost:8000")
        return None

def main():
    """Run all authentication tests."""
    print("🚀 Starting Authentication API Tests")
    print("Make sure your FastAPI server is running on http://localhost:8000")
    
    # Test registration
    registration_result = test_user_registration()
    if not registration_result:
        print("❌ Registration failed. Stopping tests.")
        return
    
    access_token = registration_result.get("access_token")
    if not access_token:
        print("❌ No access token received. Stopping tests.")
        return
    
    # Test login with the same credentials
    login_result = test_user_login()
    if login_result:
        access_token = login_result.get("access_token")
    
    # Test other endpoints
    test_get_current_user(access_token)
    test_update_profile(access_token)
    test_update_password(access_token)
    test_update_email(access_token)
    test_refresh_token(access_token)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main() 