from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timedelta

from app.core.data.document_store import document_store
from app.core.response.generative_responder import GenerativeResponder
from app.core.auth.optional_auth import get_user_with_usage_tracking, create_limit_exceeded_response
from app.logger.app_logger import app_logger

router = APIRouter()


def get_last_uploaded_document_id(conversation_id: str) -> Optional[str]:
    """
    Get the most recently uploaded document ID from conversation context.

    Args:
        conversation_id: Conversation ID to check

    Returns:
        Document ID of the last uploaded document, or None if not found
    """
    app_logger.log_info(f"[DocumentQA] Getting last uploaded document ID for conversation: {conversation_id}")

    try:
        app_logger.log_debug("[DocumentQA] Importing ConversationManager")
        from app.conversations.conversation_handler import ConversationManager

        app_logger.log_debug(f"[DocumentQA] Retrieving conversation: {conversation_id}")
        conv = ConversationManager.get_conversation(conversation_id)
        messages = conv.get('messages', [])
        app_logger.log_debug(f"[DocumentQA] Found {len(messages)} messages in conversation")

        # Look through messages in reverse order (most recent first)
        for i, msg in enumerate(reversed(messages)):
            app_logger.log_debug(f"[DocumentQA] Checking message {i} for document uploads")

            # Check attachments for document uploads
            attachments = msg.get('attachments', [])
            app_logger.log_debug(f"[DocumentQA] Message has {len(attachments)} attachments")

            for attachment in attachments:
                if attachment.get('type') == 'document' and attachment.get('document_id'):
                    doc_id = attachment['document_id']
                    app_logger.log_info(f"[DocumentQA] Found last uploaded document: {doc_id} ({attachment.get('filename')})")
                    return doc_id

            # Also check sidebar_info for document uploads
            sidebar_info = msg.get('sidebar_info', {})
            if sidebar_info.get('type') == 'document_upload' and sidebar_info.get('document_id'):
                doc_id = sidebar_info['document_id']
                app_logger.log_info(f"[DocumentQA] Found last uploaded document in sidebar_info: {doc_id}")
                return doc_id

        app_logger.log_info(f"[DocumentQA] No uploaded documents found in conversation {conversation_id}")
        return None

    except Exception as e:
        app_logger.log_error(f"[DocumentQA] Error getting last uploaded document from conversation {conversation_id}: {e}")
        return None


def get_recent_uploaded_document_ids(conversation_id: str, limit: int = 5) -> List[str]:
    """
    Get up to `limit` most recently uploaded document IDs from conversation context.
    """
    app_logger.log_info(f"[DocumentQA] Getting recent uploaded document IDs for conversation: {conversation_id} (limit: {limit})")

    ids: List[str] = []
    try:
        app_logger.log_debug("[DocumentQA] Importing ConversationManager for recent uploads")
        from app.conversations.conversation_handler import ConversationManager

        app_logger.log_debug(f"[DocumentQA] Retrieving conversation for recent uploads: {conversation_id}")
        conv = ConversationManager.get_conversation(conversation_id)
        messages = conv.get('messages', [])
        app_logger.log_debug(f"[DocumentQA] Processing {len(messages)} messages for recent uploads")

        for i, msg in enumerate(reversed(messages)):
            app_logger.log_debug(f"[DocumentQA] Processing message {i} for document IDs")

            # From attachments
            for attachment in msg.get('attachments', []):
                if attachment.get('type') == 'document':
                    doc_id = attachment.get('document_id') or attachment.get('documentId')
                    if doc_id and doc_id not in ids:
                        ids.append(doc_id)
                        app_logger.log_debug(f"[DocumentQA] Added document ID from attachment: {doc_id}")
                        if len(ids) >= limit:
                            app_logger.log_debug(f"[DocumentQA] Reached limit of {limit} documents")
                            return ids

            # From sidebar_info
            sidebar = msg.get('sidebar_info', {})
            if sidebar.get('type') == 'document_upload':
                doc_id = sidebar.get('document_id') or sidebar.get('documentId')
                if doc_id and doc_id not in ids:
                    ids.append(doc_id)
                    app_logger.log_debug(f"[DocumentQA] Added document ID from sidebar: {doc_id}")
                    if len(ids) >= limit:
                        app_logger.log_debug(f"[DocumentQA] Reached limit of {limit} documents")
                        return ids

        app_logger.log_info(f"[DocumentQA] Found {len(ids)} recent uploaded documents")
        return ids

    except Exception as e:
        app_logger.log_error(f"[DocumentQA] Error getting recent uploaded documents: {e}")
        return ids


class DocumentQuery(BaseModel):
    """Model for document query requests."""
    query: str
    document_ids: Optional[List[str]] = None
    search_all: bool = True
    max_results: int = 5
    conversation_id: Optional[str] = None


class DocumentAnalysis(BaseModel):
    """Model for document analysis requests."""
    document_id: str
    analysis_type: str  # "summary", "key_points", "questions", "structure"


@router.post("/query")
async def query_documents(request: DocumentQuery, http_request: Request) -> JSONResponse:
    """
    Query documents and get AI-powered answers.
    Supports both authenticated and unauthenticated users with usage tracking.
    
    Args:
        request: Query request with question and document selection
        http_request: HTTP request for authentication
        
    Returns:
        JSONResponse containing answer and relevant document information
    """
    start_time = time.monotonic()
    
    try:
        # Authenticate and track usage
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "document_qa"
        )
        
        app_logger.log_info(f"[Document QA] Query from {identifier}: '{request.query[:50]}...'")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            app_logger.log_warning(f"[DocumentQA] Usage limit exceeded for {identifier}")
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=429,
                content=limit_response,
                headers=response_headers
            )

        # Check if this is a generic query about documents
        app_logger.log_debug("[DocumentQA] Analyzing query type")
        generic_queries = [
            "what is this document about",
            "tell me about this document", 
            "what is this about",
            "can you tell me more about this document",
            "what are the main topics",
            "summarize this document",
            "what does this document contain",
            "what is in this document",
            "describe this document",
            "overview of this document"
        ]
        
        # Also check for common summarization requests
        summarization_indicators = [
            "summarize",
            "summary",
            "summarise",
            "brief",
            "overview",
            "what is this about",
            "tell me about",
            "describe"
        ]
        
        is_generic_query = any(gq in request.query.lower() for gq in generic_queries) or \
                          any(indicator in request.query.lower() for indicator in summarization_indicators)

        app_logger.log_debug(f"[DocumentQA] Query analysis result - is_generic_query: {is_generic_query}")

        # If it's a generic query, prefer provided document_ids; otherwise check recent uploads
        if is_generic_query:
            app_logger.log_info(f"[DocumentQA] Generic query detected: '{request.query}'")
            
            if request.document_ids:
                app_logger.log_info(f"Using provided document_ids for generic query: {len(request.document_ids)} IDs")
                search_results = []
                for doc_id in request.document_ids:
                    try:
                        doc = await document_store.get_document(doc_id)
                        content = await document_store.get_document_content(doc_id)
                        if doc and content:
                            search_results.append({
                                "document": doc,
                                "relevance_score": 1.5,  # Favor explicitly selected docs
                                "matched_content": [content[:500] + "..." if len(content) > 500 else content]
                            })
                            app_logger.log_info(f"Included document for summary: {doc['filename']} (ID: {doc['_id']})")
                    except Exception as e:
                        app_logger.log_error(f"Error retrieving specified document {doc_id}: {e}")
            else:
                # If we have a conversation, get all recent uploads
                recent_ids: List[str] = []
                if request.conversation_id:
                    # For generic queries, get all recent uploaded documents in the conversation
                    recent_ids = get_recent_uploaded_document_ids(request.conversation_id, limit=max(5, request.max_results))
                    app_logger.log_info(f"Found {len(recent_ids)} recent uploaded documents for generic query: {recent_ids}")
                if recent_ids:
                    app_logger.log_info(f"Found {len(recent_ids)} recent uploaded documents in conversation; summarizing all")
                    search_results = []
                    for doc_id in recent_ids:
                        try:
                            doc = await document_store.get_document(doc_id)
                            content = await document_store.get_document_content(doc_id)
                            if doc and content:
                                search_results.append({
                                    "document": doc,
                                    "relevance_score": 1.8,  # Favor recent uploads
                                    "matched_content": [content[:500] + "..." if len(content) > 500 else content]
                                })
                                app_logger.log_info(f"Included recent uploaded document: {doc['filename']} (ID: {doc['_id']})")
                        except Exception as e:
                            app_logger.log_error(f"Error retrieving recent uploaded document {doc_id}: {e}")
                else:
                    # No recent uploads found, fall back to all documents
                    app_logger.log_info("No recently uploaded documents found, getting all documents")
                    # For generic queries, always get at least 5 documents to ensure recent uploads are included
                    limit_for_generic = max(5, request.max_results)
                    all_documents = await document_store.list_documents(limit=limit_for_generic)
                    app_logger.log_info(f"Found {len(all_documents)} documents from list_documents call:")
                    for i, doc in enumerate(all_documents):
                        app_logger.log_info(f"  {i+1}. {doc['filename']} (ID: {doc['_id']}, uploaded: {doc.get('upload_date', 'unknown')})")                
                    search_results = []
                    for doc in all_documents:
                        content = await document_store.get_document_content(doc["_id"])
                        if content:
                            search_results.append({
                                "document": doc,
                                "relevance_score": 1.0,  # Default score for generic queries
                                "matched_content": [content[:500] + "..." if len(content) > 500 else content]
                            })
        else:
            # Search for relevant documents
            if request.search_all:
                # Search across all documents
                app_logger.log_info(f"Searching all documents for query: '{request.query}'")
                search_results = await document_store.search_documents(
                    query=request.query,
                    limit=request.max_results
                )
                app_logger.log_info(f"Found {len(search_results)} search results")
            else:
                # Search only in specified documents
                app_logger.log_info(f"Searching specified documents for query: '{request.query}'")
                search_results = []
                for doc_id in request.document_ids or []:
                    # Get document content
                    content = await document_store.get_document_content(doc_id)
                    if content:
                        # Simple keyword matching for specified documents
                        query_words = request.query.lower().split()
                        score = sum(1 for word in query_words if word in content.lower())
                        if score > 0:
                            doc_metadata = await document_store.get_document(doc_id)
                            if doc_metadata:
                                search_results.append({
                                    "document": doc_metadata,
                                    "relevance_score": score,
                                    "matched_content": [content[:500] + "..." if len(content) > 500 else content]
                                })
        
        if not search_results:
            app_logger.log_warning(f"[DocumentQA] No search results found for query: '{request.query}'")
            response_data = {
                "status": "success",
                "answer": "I couldn't find any relevant documents to answer your question. Please try uploading some documents first or rephrase your question.",
                "sources": [],
                "query": request.query,
                "processing_time_seconds": round(time.monotonic() - start_time, 2)
            }
            
            # Add usage warning for unauthenticated users
            if usage_info.get("tier") == "unauth":
                remaining = usage_info.get("remaining", 0)
                if remaining <= 2:
                    response_data["usage_warning"] = {
                        "remaining_requests": remaining,
                        "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                        "upgrade_prompt": "Sign up for free to continue using our document QA service."
                    }
            
            return JSONResponse(
                content=response_data,
                status_code=200,
                headers=response_headers
            )
        
        # Prepare context from relevant documents
        app_logger.log_info(f"[DocumentQA] Preparing context from {len(search_results)} search results")
        context_parts = []
        sources = []
        
        for result in search_results:
            doc = result["document"]
            sources.append({
                "document_id": doc["_id"],
                "filename": doc["filename"],
                "relevance_score": result["relevance_score"],
                "extracted_title": doc.get("metadata", {}).get("original_filename", doc["filename"])
            })
            
            app_logger.log_info(f"Found document: {doc['filename']} (ID: {doc['_id']}) with relevance score: {result['relevance_score']}")
            
            # Add relevant content snippets
            for chunk in result.get("matched_content", [])[:2]:  # Top 2 chunks
                context_parts.append(f"From document '{doc['filename']}':\n{chunk}\n")
        
        context = "\n".join(context_parts)
        
        # Create AI prompt for answering
        if is_generic_query:
            prompt = f"""
You are a helpful AI assistant that provides information about uploaded documents.

User Question: {request.query}

Available Documents:
{context}

Please provide a comprehensive overview of the uploaded documents. For each document, include:
1. **Document Title**: The filename and any extracted title
2. **Content Summary**: What the document appears to be about based on the content
3. **Key Topics**: Main themes, subjects, or concepts covered
4. **Document Type**: Whether it appears to be a guide, specification, prompt, etc.
5. **Key Points**: Important details, insights, or information from the document

If there are multiple documents, provide an overview of each one separately.

For the overall collection, mention:
- How many documents are available ({len(sources)} documents)
- Any common themes across documents
- Suggestions for specific questions the user could ask about particular topics

Be informative and helpful, even if the content snippets are limited. If you can't determine the content clearly, mention that and suggest the user ask more specific questions.

Answer:
"""
        else:
            prompt = f"""
You are a helpful AI assistant that answers questions based on the provided document content.

User Question: {request.query}

Relevant Document Content:
{context}

Please provide a comprehensive answer based on the document content above. If the documents don't contain enough information to fully answer the question, say so and provide what information you can find. Be accurate and cite the source documents when possible.

Answer:
"""
        
        # Generate answer using AI with proper cleanup
        app_logger.log_debug(f"[DocumentQA] Creating AI prompt, length: {len(prompt)} characters")
        app_logger.log_debug("[DocumentQA] Starting AI response generation")
        async with GenerativeResponder() as responder:
            answer = await responder.generate_text(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
        app_logger.log_debug(f"[DocumentQA] AI response generated, length: {len(answer)} characters")
        
        duration = time.monotonic() - start_time
        app_logger.log_info(f"[DocumentQA] Query processing completed in {duration:.2f}s with {len(sources)} sources")

        response_data = {
            "status": "success",
            "answer": answer,
            "sources": sources,
            "query": request.query,
            "processing_time_seconds": round(duration, 2),
            "documents_consulted": len(sources)
        }
        
        # Add usage warning for unauthenticated users
        if usage_info.get("tier") == "unauth":
            remaining = usage_info.get("remaining", 0)
            if remaining <= 2:
                response_data["usage_warning"] = {
                    "remaining_requests": remaining,
                    "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                    "upgrade_prompt": "Sign up for free to continue using our document QA service."
                }
        
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers=response_headers
        )
        
    except HTTPException as e:
        if e.status_code == 429:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e
    except Exception as e:
        app_logger.log_error(f"Document query failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "document_query_failed", "message": f"Failed to process query: {str(e)}"}
        )


@router.post("/analyze")
async def analyze_document(request: DocumentAnalysis, http_request: Request) -> JSONResponse:
    """
    Analyze a specific document and provide insights.
    Supports both authenticated and unauthenticated users with usage tracking.

    Args:
        request: Analysis request with document ID and analysis type
        http_request: HTTP request for authentication

    Returns:
        JSONResponse containing analysis results
    """
    start_time = time.monotonic()
    app_logger.log_info(f"[DocumentQA] Starting document analysis")
    app_logger.log_debug(f"[DocumentQA] Analysis request - document_id: {request.document_id}, type: {request.analysis_type}")

    try:
        # Authenticate and track usage
        app_logger.log_debug("[DocumentQA] Authenticating user for document analysis")
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "document_analyze"
        )

        app_logger.log_info(f"[DocumentQA] Document analysis request from {identifier}: {request.analysis_type} for doc {request.document_id}")
        app_logger.log_debug(f"[DocumentQA] Analysis usage info: {usage_info}")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            app_logger.log_warning(f"[DocumentQA] Analysis usage limit exceeded for {identifier}")
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=429,
                content=limit_response,
                headers=response_headers
            )

        # Get document content
        app_logger.log_debug(f"[DocumentQA] Retrieving document content for: {request.document_id}")
        content = await document_store.get_document_content(request.document_id)
        if not content:
            app_logger.log_error(f"[DocumentQA] Document content not found: {request.document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        app_logger.log_debug(f"[DocumentQA] Document content retrieved, length: {len(content)} characters")

        # Get document metadata
        app_logger.log_debug(f"[DocumentQA] Retrieving document metadata for: {request.document_id}")
        doc_metadata = await document_store.get_document(request.document_id)
        if not doc_metadata:
            app_logger.log_error(f"[DocumentQA] Document metadata not found: {request.document_id}")
            raise HTTPException(status_code=404, detail="Document metadata not found")

        app_logger.log_debug(f"[DocumentQA] Document metadata retrieved for: {doc_metadata['filename']}")
        
        # Create analysis prompt based on type
        if request.analysis_type == "summary":
            prompt = f"""
Please provide a comprehensive summary of the following document:

Document: {doc_metadata['filename']}
Content:
{content[:3000]}...

Please include:
1. Main topics and themes
2. Key points and insights
3. Overall purpose or objective
4. Target audience (if apparent)

Summary:
"""
        elif request.analysis_type == "key_points":
            prompt = f"""
Please extract the key points from the following document:

Document: {doc_metadata['filename']}
Content:
{content[:3000]}...

Please identify and list:
1. Main concepts and ideas
2. Important facts and figures
3. Key takeaways
4. Critical insights

Key Points:
"""
        elif request.analysis_type == "questions":
            prompt = f"""
Based on the following document, generate thoughtful questions that would help someone understand the content better:

Document: {doc_metadata['filename']}
Content:
{content[:3000]}...

Please generate:
1. Comprehension questions (to check understanding)
2. Analysis questions (to think deeper about the content)
3. Application questions (to apply the knowledge)
4. Critical thinking questions (to evaluate the content)

Questions:
"""
        elif request.analysis_type == "structure":
            prompt = f"""
Please analyze the structure and organization of the following document:

Document: {doc_metadata['filename']}
Content:
{content[:3000]}...

Please identify:
1. Document structure and sections
2. Flow of information
3. Logical organization
4. How ideas are connected
5. Any structural patterns or themes

Structure Analysis:
"""
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported analysis type: {request.analysis_type}")
        
        # Generate analysis using AI with proper cleanup
        app_logger.log_debug(f"[DocumentQA] Generated analysis prompt for {request.analysis_type}, length: {len(prompt)} characters")
        app_logger.log_debug("[DocumentQA] Starting AI analysis generation")
        async with GenerativeResponder() as responder:
            analysis = await responder.generate_text(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
        app_logger.log_debug(f"[DocumentQA] Analysis generated, length: {len(analysis)} characters")
        
        duration = time.monotonic() - start_time
        app_logger.log_info(f"[DocumentQA] Document analysis completed in {duration:.2f}s for {request.analysis_type}")

        response_data = {
            "status": "success",
            "analysis_type": request.analysis_type,
            "document_id": request.document_id,
            "filename": doc_metadata['filename'],
            "analysis": analysis,
            "processing_time_seconds": round(duration, 2)
        }
        
        # Add usage warning for unauthenticated users
        if usage_info.get("tier") == "unauth":
            remaining = usage_info.get("remaining", 0)
            if remaining <= 2:
                response_data["usage_warning"] = {
                    "remaining_requests": remaining,
                    "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                    "upgrade_prompt": "Sign up for free to continue using our document analysis service."
                }
        
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers=response_headers
        )
        
    except HTTPException as e:
        if e.status_code in [404, 400]:
            raise e
        elif e.status_code == 429:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e
    except Exception as e:
        app_logger.log_error(f"Document analysis failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "document_analysis_failed", "message": f"Failed to analyze document: {str(e)}"}
        )


@router.get("/suggestions/{document_id}")
async def get_document_suggestions(document_id: str, http_request: Request) -> JSONResponse:
    """
    Get AI-generated suggestions for what users can do with a specific document.
    Supports both authenticated and unauthenticated users with usage tracking.

    Args:
        document_id: Document ID
        http_request: HTTP request for authentication

    Returns:
        JSONResponse containing suggestions
    """
    start_time = time.monotonic()
    app_logger.log_info(f"[DocumentQA] Starting document suggestions generation")
    app_logger.log_debug(f"[DocumentQA] Suggestions request for document: {document_id}")

    try:
        # Authenticate and track usage
        app_logger.log_debug("[DocumentQA] Authenticating user for document suggestions")
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "document_suggestions"
        )

        app_logger.log_info(f"[DocumentQA] Document suggestions request from {identifier} for doc {document_id}")
        app_logger.log_debug(f"[DocumentQA] Suggestions usage info: {usage_info}")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            app_logger.log_warning(f"[DocumentQA] Suggestions usage limit exceeded for {identifier}")
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=429,
                content=limit_response,
                headers=response_headers
            )

        # Get document content
        app_logger.log_debug(f"[DocumentQA] Retrieving document content for suggestions: {document_id}")
        content = await document_store.get_document_content(document_id)
        if not content:
            app_logger.log_error(f"[DocumentQA] Document content not found for suggestions: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")

        app_logger.log_debug(f"[DocumentQA] Document content retrieved for suggestions, length: {len(content)} characters")

        # Get document metadata
        app_logger.log_debug(f"[DocumentQA] Retrieving document metadata for suggestions: {document_id}")
        doc_metadata = await document_store.get_document(document_id)
        if not doc_metadata:
            app_logger.log_error(f"[DocumentQA] Document metadata not found for suggestions: {document_id}")
            raise HTTPException(status_code=404, detail="Document metadata not found")

        app_logger.log_debug(f"[DocumentQA] Document metadata retrieved for suggestions: {doc_metadata['filename']}")
        
        # Create suggestions prompt
        prompt = f"""
Based on the following document, suggest 5-7 specific things users could do or ask about this content:

Document: {doc_metadata['filename']}
Content Preview:
{content[:2000]}...

Please provide suggestions in these categories:
1. **Questions to Ask**: Specific questions about the content
2. **Analysis Requests**: Types of analysis they could request
3. **Learning Activities**: Educational activities or exercises
4. **Related Topics**: Topics they might want to explore further

Format your response as a clear list with categories.

Suggestions:
"""
        
        # Generate suggestions using AI with proper cleanup
        app_logger.log_debug(f"[DocumentQA] Generated suggestions prompt, length: {len(prompt)} characters")
        app_logger.log_debug("[DocumentQA] Starting AI suggestions generation")
        async with GenerativeResponder() as responder:
            suggestions = await responder.generate_text(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
        app_logger.log_debug(f"[DocumentQA] Suggestions generated, length: {len(suggestions)} characters")
        
        duration = time.monotonic() - start_time
        app_logger.log_info(f"[DocumentQA] Document suggestions completed in {duration:.2f}s")

        response_data = {
            "status": "success",
            "document_id": document_id,
            "filename": doc_metadata['filename'],
            "suggestions": suggestions,
            "processing_time_seconds": round(duration, 2)
        }
        
        # Add usage warning for unauthenticated users
        if usage_info.get("tier") == "unauth":
            remaining = usage_info.get("remaining", 0)
            if remaining <= 2:
                response_data["usage_warning"] = {
                    "remaining_requests": remaining,
                    "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                    "upgrade_prompt": "Sign up for free to continue using our document suggestions service."
                }
        
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers=response_headers
        )
        
    except HTTPException as e:
        if e.status_code == 404:
            raise e
        elif e.status_code == 429:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e
    except Exception as e:
        app_logger.log_error(f"Document suggestions failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "document_suggestions_failed", "message": f"Failed to generate suggestions: {str(e)}"}
        )


@router.get("/search")
async def search_documents(query: str, http_request: Request, limit: int = 10) -> JSONResponse:
    """
    Search documents by keyword and return relevant results.
    Supports both authenticated and unauthenticated users with usage tracking.

    Args:
        query: Search query
        http_request: HTTP request for authentication
        limit: Maximum number of results

    Returns:
        JSONResponse containing search results
    """
    start_time = time.monotonic()
    app_logger.log_info(f"[DocumentQA] Starting document search")
    app_logger.log_debug(f"[DocumentQA] Search parameters - query length: {len(query)}, limit: {limit}")
    app_logger.log_debug(f"[DocumentQA] Search query: '{query}'")

    try:
        # Authenticate and track usage
        app_logger.log_debug("[DocumentQA] Authenticating user for document search")
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "document_search"
        )

        app_logger.log_info(f"[DocumentQA] Document search request from {identifier}: '{query[:50]}...' (limit: {limit})")
        app_logger.log_debug(f"[DocumentQA] Search usage info: {usage_info}")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            app_logger.log_warning(f"[DocumentQA] Search usage limit exceeded for {identifier}")
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=429,
                content=limit_response,
                headers=response_headers
            )

        # Search documents
        app_logger.log_debug(f"[DocumentQA] Executing document search with query: '{query}' and limit: {limit}")
        search_results = await document_store.search_documents(
            query=query,
            limit=limit
        )
        app_logger.log_debug(f"[DocumentQA] Search completed, found {len(search_results)} results")
        
        # Format results
        app_logger.log_debug("[DocumentQA] Formatting search results")
        formatted_results = []
        for i, result in enumerate(search_results):
            doc = result["document"]
            formatted_result = {
                "document_id": doc["_id"],
                "filename": doc["filename"],
                "relevance_score": result["relevance_score"],
                "extracted_title": doc.get("metadata", {}).get("original_filename", doc["filename"]),
                "file_type": doc.get("file_type"),
                "upload_date": doc.get("upload_date"),
                "matched_content": result.get("matched_content", [])
            }
            formatted_results.append(formatted_result)
            app_logger.log_debug(f"[DocumentQA] Formatted result {i}: {doc['filename']} (score: {result['relevance_score']})")
        
        duration = time.monotonic() - start_time
        app_logger.log_info(f"[DocumentQA] Document search completed in {duration:.2f}s with {len(formatted_results)} results")

        response_data = {
            "status": "success",
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "processing_time_seconds": round(duration, 2)
        }
        
        # Add usage warning for unauthenticated users
        if usage_info.get("tier") == "unauth":
            remaining = usage_info.get("remaining", 0)
            if remaining <= 2:
                response_data["usage_warning"] = {
                    "remaining_requests": remaining,
                    "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                    "upgrade_prompt": "Sign up for free to continue using our document search service."
                }
        
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers=response_headers
        )
        
    except HTTPException as e:
        if e.status_code == 429:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e
    except Exception as e:
        app_logger.log_error(f"Document search failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "document_search_failed", "message": f"Failed to search documents: {str(e)}"}
        ) 