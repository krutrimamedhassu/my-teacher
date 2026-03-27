#!/usr/bin/env python3
"""
Test script for the Delete Conversation API

This script demonstrates how to use the delete conversation endpoint:
- Create a conversation
- Delete the conversation
- Verify the conversation is marked as deleted

Make sure to:
1. Set up your server and MongoDB connection
2. Install dependencies: pip install -r requirements.txt
3. Start the FastAPI server: python -m app.main
"""

import requests
import json
from typing import Optional, List, Any

BASE_URL = "http://localhost:8000/api/v1/conversations"

def print_curl_command(method: str, endpoint: str, data: Optional[dict] = None, title: str = ""):
    """Print the curl command for manual testing"""
    curl_cmd = f"curl -X {method.upper()} '{BASE_URL}{endpoint}'"
    if data:
        curl_cmd += f" \\\n  -H 'Content-Type: application/json' \\\n  -d '{json.dumps(data)}'"
    print(f"\n🔗 {title} CURL Command:")
    print(f"{curl_cmd}")

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
    print_curl_command("POST", "/", data, "Create Conversation")
    response = requests.post(BASE_URL + "/", json=data)
    print_response(response, "Create Conversation")
    return response.json() if response.status_code == 200 else None

def test_delete_conversation(conversation_id: str):
    print("\n🧪 Testing Delete Conversation...")
    print_curl_command("DELETE", f"/{conversation_id}", title="Delete Conversation")
    response = requests.delete(f"{BASE_URL}/{conversation_id}")
    print_response(response, "Delete Conversation")
    return response.json() if response.status_code == 200 else None

def test_get_conversation(conversation_id: str):
    print("\n🧪 Testing Get Conversation...")
    print_curl_command("GET", f"/{conversation_id}", title="Get Conversation")
    response = requests.get(f"{BASE_URL}/{conversation_id}")
    print_response(response, "Get Conversation")
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
    print_curl_command("POST", f"/{conversation_id}/messages", data, "Add Message")
    response = requests.post(f"{BASE_URL}/{conversation_id}/messages", json=data)
    print_response(response, "Add Message")
    return response.json() if response.status_code == 200 else None

def main():
    print("🚀 Starting Delete Conversation API Tests")
    print("Make sure your FastAPI server is running on http://localhost:8000")

    # Test: Create a conversation to delete
    user_id = "user123"
    username = "testuser"
    conv = test_create_conversation(user_id=user_id, username=username, title="Conversation to Delete")
    if not conv:
        print("❌ Failed to create conversation. Stopping tests.")
        return
    conversation_id = conv["conversation_id"]

    # Test: Add some messages to the conversation
    test_add_message(conversation_id, sender_id=user_id, sender_username=username, role="user", text="Hello, this conversation will be deleted!")
    test_add_message(conversation_id, sender_id=None, sender_username="assistant", role="assistant", text="I understand this conversation will be deleted.")

    # Test: Get the conversation before deletion
    print("\n📋 Getting conversation before deletion...")
    test_get_conversation(conversation_id)

    # Test: Delete the conversation
    delete_result = test_delete_conversation(conversation_id)
    if not delete_result:
        print("❌ Failed to delete conversation. Stopping tests.")
        return

    # Verify the delete response
    if delete_result.get("detail") == "Conversation deleted":
        print("✅ Conversation deleted successfully!")
        if delete_result.get("conversation", {}).get("deleted") is True:
            print("✅ Conversation marked as deleted!")
        if delete_result.get("conversation", {}).get("is_active") is False:
            print("✅ Conversation marked as inactive!")
    else:
        print("❌ Unexpected delete response")

    # Test: Get the conversation after deletion to verify it's marked as deleted
    print("\n📋 Getting conversation after deletion...")
    get_result = test_get_conversation(conversation_id)
    if get_result:
        if get_result.get("deleted") is True:
            print("✅ Conversation correctly marked as deleted!")
        else:
            print("❌ Conversation not marked as deleted")
        
        if get_result.get("is_active") is False:
            print("✅ Conversation correctly marked as inactive!")
        else:
            print("❌ Conversation not marked as inactive")

    # Test: Try to delete a non-existent conversation
    print("\n🧪 Testing Delete Non-existent Conversation...")
    non_existent_id = "non-existent-conversation-id"
    print_curl_command("DELETE", f"/{non_existent_id}", title="Delete Non-existent Conversation")
    delete_nonexistent = test_delete_conversation(non_existent_id)
    if delete_nonexistent is None:
        print("✅ Correctly handled non-existent conversation deletion")

    print("\n✅ All delete conversation tests completed!")

if __name__ == "__main__":
    main() 