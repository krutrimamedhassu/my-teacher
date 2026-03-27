#!/usr/bin/env python3
"""
Test script for the Conversations API

This script demonstrates how to use the conversation endpoints:
- Create conversation (user and anonymous)
- Add message
- Get conversation
- List conversations (user and anonymous)

Make sure to:
1. Set up your server and MongoDB connection
2. Install dependencies: pip install -r requirements.txt
3. Start the FastAPI server: python -m app.main
"""

import requests
import json
from typing import Optional, List, Any

BASE_URL = "http://localhost:8000/api/v1/conversations"

def print_response(response: requests.Response, title: str):
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception:
        print(f"Response: {response.text}")
    print(f"{'='*50}")

def test_create_conversation(user_id: Optional[str] = None, username: Optional[str] = None, title: Optional[str] = None):
    print("\n🧪 Testing Create Conversation...")
    data = {"user_id": user_id, "username": username, "title": title}
    response = requests.post(BASE_URL + "/", json=data)
    print_response(response, "Create Conversation")
    return response.json() if response.status_code == 200 else None

def test_create_conversation_with_id(conversation_id: Optional[str] = None, user_id: Optional[str] = None, username: Optional[str] = None, title: Optional[str] = None):
    print("\n🧪 Testing Create Conversation with Specific ID...")
    data = {"conversation_id": conversation_id, "user_id": user_id, "username": username, "title": title}
    response = requests.post(BASE_URL + "/create_id", json=data)
    print_response(response, "Create Conversation with ID")
    return response.json() if response.status_code == 200 else None

def test_add_message(conversation_id: str, sender_id: Optional[str], sender_username: Optional[str], role: str, text: str, attachments: Optional[List[Any]] = None):
    print("\n🧪 Testing Add Message...")
    data = {
        "sender_id": sender_id,
        "sender_username": sender_username,
        "role": role,
        "text": text,
        "attachments": attachments or []
    }
    response = requests.post(f"{BASE_URL}/{conversation_id}/messages", json=data)
    print_response(response, "Add Message")
    return response.json() if response.status_code == 200 else None

def test_get_conversation(conversation_id: str):
    print("\n🧪 Testing Get Conversation...")
    response = requests.get(f"{BASE_URL}/{conversation_id}")
    print_response(response, "Get Conversation")
    return response.json() if response.status_code == 200 else None

def test_list_conversations_for_user(user_id: str):
    print("\n🧪 Testing List Conversations for User...")
    response = requests.get(f"{BASE_URL}/user/{user_id}")
    print_response(response, "List Conversations for User")
    return response.json() if response.status_code == 200 else None

def test_list_conversations_anonymous():
    print("\n🧪 Testing List Anonymous Conversations...")
    response = requests.get(f"{BASE_URL}/anonymous")
    print_response(response, "List Anonymous Conversations")
    return response.json() if response.status_code == 200 else None

def main():
    print("🚀 Starting Conversations API Tests")
    print("Make sure your FastAPI server is running on http://localhost:8000")

    # Test: Create conversation as user
    user_id = "user123"
    username = "testuser"
    conv = test_create_conversation(user_id=user_id, username=username, title="User Conversation")
    if not conv:
        print("❌ Failed to create user conversation. Stopping tests.")
        return
    conversation_id = conv["conversation_id"]

    # Test: Add message as user
    test_add_message(conversation_id, sender_id=user_id, sender_username=username, role="user", text="Hello from user!")
    test_add_message(conversation_id, sender_id=None, sender_username="assistant", role="assistant", text="Hello, how can I help you?")

    # Test: Get conversation
    test_get_conversation(conversation_id)

    # Test: List conversations for user
    test_list_conversations_for_user(user_id)

    # Test: Create anonymous conversation
    anon_conv = test_create_conversation()
    if not anon_conv:
        print("❌ Failed to create anonymous conversation. Stopping tests.")
        return
    anon_conversation_id = anon_conv["conversation_id"]

    # Test: Add message as anonymous
    test_add_message(anon_conversation_id, sender_id=None, sender_username="Anonymous", role="user", text="Hi, I'm anonymous!")
    test_add_message(anon_conversation_id, sender_id=None, sender_username="assistant", role="assistant", text="Hello anonymous user!")

    # Test: Get anonymous conversation
    test_get_conversation(anon_conversation_id)

    # Test: List anonymous conversations
    test_list_conversations_anonymous()

    # Test: Create conversation with a specific conversation_id
    custom_conversation_id = "my-custom-id-123"
    custom_conv = test_create_conversation_with_id(conversation_id=custom_conversation_id, user_id="user999", username="customuser", title="Custom ID Conversation")
    if custom_conv:
        # Add a message to the custom conversation
        test_add_message(custom_conversation_id, sender_id="user999", sender_username="customuser", role="user", text="Hello from custom ID!")
        # Fetch the custom conversation
        test_get_conversation(custom_conversation_id)

    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main() 