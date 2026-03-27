#!/usr/bin/env python3
"""
Test script to verify document search functionality
"""

import asyncio
import aiohttp
import json

async def test_document_search():
    """Test document search functionality"""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("🔍 Testing Document Search Functionality")
        print("=" * 50)
        
        # Test 1: List all documents
        print("\n1. Listing all documents...")
        try:
            async with session.get(f"{base_url}/api/v1/upload/documents") as response:
                result = await response.json()
                if response.status == 200:
                    documents = result.get('documents', [])
                    print(f"✅ Found {len(documents)} documents:")
                    for doc in documents:
                        print(f"  - {doc['filename']} (ID: {doc['_id']})")
                    
                    if documents:
                        # Test 2: Search for documents
                        print(f"\n2. Testing document search...")
                        search_queries = [
                            "document",
                            "ai",
                            "engineer",
                            "Common AI engineer"
                        ]
                        
                        for query in search_queries:
                            print(f"\n   Searching for: '{query}'")
                            try:
                                async with session.get(
                                    f"{base_url}/api/v1/document-qa/search",
                                    params={"query": query, "limit": 5}
                                ) as search_response:
                                    search_result = await search_response.json()
                                    if search_response.status == 200:
                                        results = search_result.get('results', [])
                                        print(f"   ✅ Found {len(results)} results")
                                        for doc in results:
                                            print(f"     - {doc['filename']} (Score: {doc['relevance_score']:.2f})")
                                    else:
                                        print(f"   ❌ Search failed: {search_result}")
                            except Exception as e:
                                print(f"   ❌ Search error: {e}")
                        
                        # Test 3: Query documents
                        print(f"\n3. Testing document query...")
                        test_queries = [
                            "What is this document about?",
                            "Tell me about this document",
                            "What are the main topics?",
                            "document"
                        ]
                        
                        for query in test_queries:
                            print(f"\n   Querying: '{query}'")
                            try:
                                payload = {
                                    "query": query,
                                    "search_all": True,
                                    "max_results": 5
                                }
                                async with session.post(
                                    f"{base_url}/api/v1/document-qa/query",
                                    json=payload
                                ) as query_response:
                                    query_result = await query_response.json()
                                    if query_response.status == 200:
                                        answer = query_result.get('answer', '')
                                        sources = query_result.get('sources', [])
                                        print(f"   ✅ Answer: {answer[:100]}...")
                                        print(f"   📚 Sources: {len(sources)} documents")
                                        for source in sources:
                                            print(f"     - {source['filename']} (Score: {source['relevance_score']:.2f})")
                                    else:
                                        print(f"   ❌ Query failed: {query_result}")
                            except Exception as e:
                                print(f"   ❌ Query error: {e}")
                    else:
                        print("❌ No documents found. Please upload some documents first.")
                else:
                    print(f"❌ Failed to list documents: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_document_search()) 