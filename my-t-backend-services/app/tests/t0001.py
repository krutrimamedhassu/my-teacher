#!/usr/bin/env python3
"""
Test script for Document Search functionality

This script demonstrates how to test the document search endpoints:
- List documents
- Search documents
- Query documents with AI

Make sure to:
1. Set up your server and MongoDB connection
2. Install dependencies: pip install -r requirements.txt
3. Start the FastAPI server: python -m app.main
4. Upload some documents first
"""

import requests
import json
from typing import Optional, List, Any

BASE_URL = "http://localhost:8000/api/v1"


def print_response(response: requests.Response, title: str):
    print(f"\n{'=' * 50}")
    print(f"{title}")
    print(f"{'=' * 50}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception:
        print(f"Response: {response.text}")
    print(f"{'=' * 50}")


def test_list_documents():
    print("\n🧪 Testing List Documents...")
    response = requests.get(f"{BASE_URL}/upload/documents")
    print_response(response, "List Documents")
    return response.json() if response.status_code == 200 else None


def test_search_documents(query: str, limit: int = 5):
    print(f"\n🧪 Testing Search Documents for: '{query}'...")
    params = {"query": query, "limit": limit}
    response = requests.get(f"{BASE_URL}/document-qa/search", params=params)
    print_response(response, f"Search Documents - '{query}'")
    return response.json() if response.status_code == 200 else None


def test_query_documents(query: str, search_all: bool = True, max_results: int = 5):
    print(f"\n🧪 Testing Query Documents: '{query}'...")
    data = {
        "query": query,
        "search_all": search_all,
        "max_results": max_results
    }
    response = requests.post(f"{BASE_URL}/document-qa/query", json=data)
    print_response(response, f"Query Documents - '{query}'")
    return response.json() if response.status_code == 200 else None


def test_upload_document(file_path: str):
    print(f"\n🧪 Testing Upload Document: {file_path}...")
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'application/octet-stream')}
            response = requests.post(f"{BASE_URL}/upload/upload", files=files)
            print_response(response, f"Upload Document - {file_path}")
            return response.json() if response.status_code == 200 else None
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None


def main():
    print("🚀 Starting Document Search Tests")
    print("Make sure your FastAPI server is running on http://localhost:8000")
    print("Make sure you have some documents uploaded first")

    # Test 1: List all documents
    print("\n" + "=" * 60)
    print("TEST 1: LISTING ALL DOCUMENTS")
    print("=" * 60)

    documents_result = test_list_documents()
    if not documents_result:
        print("❌ Failed to list documents. Make sure you have documents uploaded.")
        return

    documents = documents_result.get('documents', [])
    if not documents:
        print("❌ No documents found. Please upload some documents first.")
        print("You can use the upload endpoint or upload through the web interface.")
        return

    print(f"✅ Found {len(documents)} documents:")
    for doc in documents:
        print(f"  - {doc['filename']} (ID: {doc['_id']})")

    # Test 2: Search for documents
    print("\n" + "=" * 60)
    print("TEST 2: SEARCHING DOCUMENTS")
    print("=" * 60)

    search_queries = [
        "document",
        "ai",
        "engineer",
        "Common AI engineer",
        "machine learning"
    ]

    for query in search_queries:
        test_search_documents(query)

    # Test 3: Query documents with AI
    print("\n" + "=" * 60)
    print("TEST 3: QUERYING DOCUMENTS WITH AI")
    print("=" * 60)

    query_tests = [
        "What is this document about?",
        "Tell me about this document",
        "What are the main topics?",
        "What is artificial intelligence?",
        "What does this document contain?"
    ]

    for query in query_tests:
        test_query_documents(query)

    # Test 4: Test specific document queries (if we have document IDs)
    if documents:
        print("\n" + "=" * 60)
        print("TEST 4: QUERYING SPECIFIC DOCUMENTS")
        print("=" * 60)

        # Use the first document for specific queries
        first_doc_id = documents[0]['_id']
        specific_queries = [
            "What is the main topic?",
            "Summarize this document",
            "What are the key points?"
        ]

        for query in specific_queries:
            print(f"\n🧪 Testing Query Specific Document: '{query}'...")
            data = {
                "query": query,
                "search_all": False,
                "document_ids": [first_doc_id],
                "max_results": 5
            }
            response = requests.post(f"{BASE_URL}/document-qa/query", json=data)
            print_response(response, f"Query Specific Document - '{query}'")

    print("\n✅ All document search tests completed!")
    print("\n💡 Tips:")
    print("- If searches return no results, try different keywords")
    print("- Make sure your documents contain the search terms")
    print("- Generic queries like 'what is this about' should return document overviews")
    print("- Specific queries should return targeted answers from document content")


if __name__ == "__main__":
    main()