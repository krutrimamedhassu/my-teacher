"""
Document Upload and Query Demo Script

This script demonstrates how to use the document upload and query system.
It shows the complete workflow from uploading documents to querying them.

Usage:
    python document_demo.py

Requirements:
    - FastAPI server running on localhost:8000
    - MongoDB connection configured
    - Sample documents to upload
"""

import asyncio
import aiohttp
import json
import os
from aiohttp import FormData
from typing import Dict, Any, List


class DocumentDemo:
    """Demo class for document upload and query functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def upload_document(self, file_path: str) -> Dict[str, Any]:
        """Upload a document to the system."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        print(f"📤 Uploading document: {file_path}")
        
        # Create form data for file upload
        data = FormData()
        data.add_field('file',
                      open(file_path, 'rb'),
                      filename=os.path.basename(file_path),
                      content_type='application/octet-stream')
        
        async with self.session.post(f"{self.base_url}/api/v1/upload/upload", data=data) as response:
            result = await response.json()
            
            if response.status == 200:
                print(f"✅ Upload successful! Document ID: {result['document_id']}")
                return result
            else:
                print(f"❌ Upload failed: {result}")
                return result
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all uploaded documents."""
        print("📋 Listing documents...")
        
        async with self.session.get(f"{self.base_url}/api/v1/upload/documents") as response:
            result = await response.json()
            
            if response.status == 200:
                documents = result['documents']
                print(f"✅ Found {len(documents)} documents:")
                for doc in documents:
                    print(f"  - {doc['filename']} (ID: {doc['_id']})")
                return documents
            else:
                print(f"❌ Failed to list documents: {result}")
                return []
    
    async def query_documents(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Query documents with a question."""
        print(f"❓ Querying documents: {question}")
        
        payload = {
            "query": question,
            "search_all": document_ids is None,
            "document_ids": document_ids,
            "max_results": 5
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/document-qa/query",
            json=payload
        ) as response:
            result = await response.json()
            
            if response.status == 200:
                print(f"✅ Query successful!")
                print(f"📄 Answer: {result['answer']}")
                print(f"📚 Sources: {len(result['sources'])} documents consulted")
                return result
            else:
                print(f"❌ Query failed: {result}")
                return result
    
    async def analyze_document(self, document_id: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze a specific document."""
        print(f"🔍 Analyzing document {document_id} with type: {analysis_type}")
        
        payload = {
            "document_id": document_id,
            "analysis_type": analysis_type
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/document-qa/analyze",
            json=payload
        ) as response:
            result = await response.json()
            
            if response.status == 200:
                print(f"✅ Analysis successful!")
                print(f"📄 Analysis: {result['analysis'][:200]}...")
                return result
            else:
                print(f"❌ Analysis failed: {result}")
                return result
    
    async def get_suggestions(self, document_id: str) -> Dict[str, Any]:
        """Get suggestions for what to do with a document."""
        print(f"💡 Getting suggestions for document {document_id}")
        
        async with self.session.get(f"{self.base_url}/api/v1/document-qa/suggestions/{document_id}") as response:
            result = await response.json()
            
            if response.status == 200:
                print(f"✅ Suggestions received!")
                print(f"💭 Suggestions: {result['suggestions'][:200]}...")
                return result
            else:
                print(f"❌ Failed to get suggestions: {result}")
                return result
    
    async def search_documents(self, query: str) -> Dict[str, Any]:
        """Search documents by content."""
        print(f"🔍 Searching documents for: {query}")
        
        async with self.session.get(
            f"{self.base_url}/api/v1/document-qa/search",
            params={"query": query, "limit": 5}
        ) as response:
            result = await response.json()
            
            if response.status == 200:
                print(f"✅ Search successful! Found {len(result['results'])} results")
                for doc in result['results']:
                    print(f"  - {doc['filename']} (Score: {doc['relevance_score']:.2f})")
                return result
            else:
                print(f"❌ Search failed: {result}")
                return result


async def create_sample_document():
    """Create a sample text document for demo purposes."""
    sample_content = """
    Introduction to Machine Learning
    
    Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves.
    
    Key Concepts:
    1. Supervised Learning: Learning from labeled training data
    2. Unsupervised Learning: Finding patterns in unlabeled data
    3. Reinforcement Learning: Learning through interaction with environment
    
    Applications:
    - Image recognition
    - Natural language processing
    - Recommendation systems
    - Autonomous vehicles
    
    The field continues to evolve rapidly with new techniques and applications being developed regularly.
    """
    
    filename = "sample_ml_document.txt"
    with open(filename, 'w') as f:
        f.write(sample_content)
    
    print(f"📝 Created sample document: {filename}")
    return filename


async def main():
    """Main demo function."""
    print("🚀 Document Upload and Query Demo")
    print("=" * 50)
    
    # Create sample document
    sample_file = await create_sample_document()
    
    async with DocumentDemo() as demo:
        try:
            # Step 1: Upload document
            upload_result = await demo.upload_document(sample_file)
            if upload_result.get('status') != 'success':
                print("❌ Demo failed at upload step")
                return
            
            document_id = upload_result['document_id']
            
            # Step 2: List documents
            await demo.list_documents()
            
            # Step 3: Get suggestions
            await demo.get_suggestions(document_id)
            
            # Step 4: Query documents
            questions = [
                "What is machine learning?",
                "What are the main types of machine learning?",
                "What are some applications of machine learning?"
            ]
            
            for question in questions:
                print("\n" + "="*50)
                await demo.query_documents(question)
            
            # Step 5: Analyze document
            analysis_types = ["summary", "key_points", "questions"]
            for analysis_type in analysis_types:
                print("\n" + "="*50)
                await demo.analyze_document(document_id, analysis_type)
            
            # Step 6: Search documents
            search_queries = ["supervised learning", "applications", "algorithms"]
            for query in search_queries:
                print("\n" + "="*50)
                await demo.search_documents(query)
            
            print("\n" + "="*50)
            print("✅ Demo completed successfully!")
            
        except Exception as e:
            print(f"❌ Demo failed with error: {e}")
        
        finally:
            # Clean up sample file
            if os.path.exists(sample_file):
                os.remove(sample_file)
                print(f"🧹 Cleaned up sample file: {sample_file}")


if __name__ == "__main__":
    print("Document Upload and Query Demo")
    print("Make sure your FastAPI server is running on localhost:8000")
    print("Press Enter to continue...")
    input()
    
    asyncio.run(main()) 