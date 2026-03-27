from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
import os
import time
from datetime import datetime

from app.logger.app_logger import app_logger
from app.core.data.doc_handler import DocumentHandler, Document, DocumentType
from app.core.data.document_store import document_store

router = APIRouter()


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    document_id: str
    filename: str
    doc_type: str
    content_preview: str
    metadata: Dict[str, Any]
    word_count: int
    page_count: Optional[int] = None
    created_at: str


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentResponse]
    total: int


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Document",
    description="Upload a document file (PDF, text, DOCX) for processing."
)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Upload a document file.
    
    Args:
        file: Document file to upload
        title: Optional title for the document
        description: Optional description of the document
        tags: Optional comma-separated tags for the document
        
    Returns:
        dict: Uploaded document information
    """
    app_logger.log_info(f"[Docs] Uploading document: {file.filename}")

    try:
        # Save the uploaded file temporarily
        file_location = f"temp_{file.filename}"
        app_logger.log_debug(f"[Docs] Saving temporary file to: {file_location}")
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
            app_logger.log_debug(f"[Docs] File saved, size: {len(content)} bytes")
        
        # Validate the document
        app_logger.log_debug(f"[Docs] Validating document: {file_location}")
        if not DocumentHandler.validate_document(file_location):
            app_logger.log_warning(f"[Docs] Document validation failed for: {file.filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document. Check file type and size."
            )
        
        # Parse the document
        document = DocumentHandler.parse_document(file_location)
        
        # Parse tags if provided
        tag_list = tags.split(",") if tags else []
        
        # Create metadata
        metadata = document.metadata or {}
        metadata.update({
            "title": title or file.filename,
            "description": description or "",
            "tags": tag_list,
            "original_filename": file.filename,
            "extracted_title": metadata.get("title", file.filename)
        })
        
        # Store the document in MongoDB
        document_id = await document_store.store_document(
            filename=file.filename,
            file_type=document.doc_type,
            file_size=len(content),
            content=document.content,
            metadata=metadata
        )
        
        # Generate a content preview
        content_preview = document.content[:200] + "..." if len(document.content) > 200 else document.content
        
        # Count words
        word_count = len(document.content.split())
        
        # Get page count from metadata if available
        page_count = metadata.get("pages")
        
        # Clean up temporary file
        try:
            os.remove(file_location)
        except Exception as e:
            app_logger.log_warning(f"Failed to remove temp file {file_location}: {e}")
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "doc_type": document.doc_type,
            "content_preview": content_preview,
            "metadata": metadata,
            "word_count": word_count,
            "page_count": page_count,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        app_logger.log_error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.post(
    "/url",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process Document from URL",
    description="Process a document from a URL (web page, PDF, etc.)."
)
async def process_url(
    url: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a document from a URL.
    
    Args:
        url: URL of the document to process
        title: Optional title for the document
        description: Optional description of the document
        tags: Optional comma-separated tags for the document
        
    Returns:
        dict: Processed document information
    """
    app_logger.log_info(f"Processing document from URL: {url}")
    
    try:
        # Parse the document from the URL
        document = DocumentHandler.parse_url(url)
        
        # In a real implementation, we would:
        # 1. Store the document in a database
        # 2. Generate a unique document ID
        # 3. Process the document for indexing, embedding, etc.
        
        # Generate a mock document ID
        import uuid
        import time
        document_id = str(uuid.uuid4())
        
        # Parse tags if provided
        tag_list = tags.split(",") if tags else []
        
        # Create metadata
        metadata = document.metadata or {}
        metadata.update({
            "title": title or url.split("/")[-1] or "Web Page",
            "description": description or "",
            "tags": tag_list,
            "source_url": url,
            "upload_time": time.time()
        })
        
        # Generate a content preview
        content_preview = document.content[:200] + "..." if len(document.content) > 200 else document.content
        
        # Count words
        word_count = len(document.content.split())
        
        return {
            "document_id": document_id,
            "filename": url.split("/")[-1] or "webpage.html",
            "doc_type": document.doc_type,
            "content_preview": content_preview,
            "metadata": metadata,
            "word_count": word_count,
            "page_count": metadata.get("pages"),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        app_logger.log_error(f"Error processing URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process URL: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document",
    description="Get information about a specific document."
)
async def get_document(document_id: str) -> Dict[str, Any]:
    """
    Get information about a document.
    
    Args:
        document_id: ID of the document to retrieve
        
    Returns:
        dict: Document information
    """
    app_logger.log_info(f"Getting document: {document_id}")
    
    try:
        # In a real implementation, this would retrieve the document from a database
        # For now, we'll return mock data
        
        return {
            "document_id": document_id,
            "filename": f"document_{document_id[:8]}.pdf",
            "doc_type": "pdf",
            "content_preview": "This is a sample document content preview...",
            "metadata": {
                "title": f"Sample Document {document_id[:8]}",
                "description": "This is a sample document for demonstration purposes.",
                "tags": ["sample", "demo"],
                "pages": 5,
                "author": "System"
            },
            "word_count": 1250,
            "page_count": 5,
            "created_at": "2023-01-01 12:00:00"
        }
    
    except Exception as e:
        app_logger.log_error(f"Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Documents",
    description="List all documents with optional filtering."
)
async def list_documents(
    page: int = 1,
    limit: int = 10,
    doc_type: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """
    List documents with optional filtering.
    
    Args:
        page: Page number for pagination
        limit: Number of documents per page
        doc_type: Filter by document type
        tag: Filter by tag
        search: Search term for document title or content
        
    Returns:
        dict: List of documents
    """
    app_logger.log_info(f"Listing documents (page={page}, limit={limit}, doc_type={doc_type}, tag={tag}, search={search})")
    
    try:
        # In a real implementation, this would query the database with filters
        # For now, we'll return mock data
        
        # Mock documents
        mock_documents = [
            {
                "document_id": f"doc{i}",
                "filename": f"document_{i}.pdf",
                "doc_type": "pdf" if i % 3 == 0 else ("docx" if i % 3 == 1 else "txt"),
                "content_preview": f"This is a preview of document {i}...",
                "metadata": {
                    "title": f"Document {i}",
                    "description": f"Description for document {i}",
                    "tags": ["sample", "document", f"tag{i}"],
                    "pages": i + 1
                },
                "word_count": (i + 1) * 500,
                "page_count": i + 1,
                "created_at": "2023-01-01 12:00:00"
            }
            for i in range(1, 21)
        ]
        
        # Apply filters
        filtered_docs = mock_documents
        
        if doc_type:
            filtered_docs = [d for d in filtered_docs if d["doc_type"] == doc_type]
            
        if tag:
            filtered_docs = [d for d in filtered_docs if tag in d["metadata"]["tags"]]
            
        if search:
            filtered_docs = [
                d for d in filtered_docs 
                if search.lower() in d["metadata"]["title"].lower() or 
                   search.lower() in d["content_preview"].lower()
            ]
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_docs = filtered_docs[start_idx:end_idx]
        
        return {
            "documents": paginated_docs,
            "total": len(filtered_docs)
        }
    
    except Exception as e:
        app_logger.log_error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )