"""
Upload endpoints with input validation and guards.

This module demonstrates the use of:
- Centralized auth dependency
- Input size and file-type guards
- Structured logging with request tracing
"""

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status, Request, Response
from typing import Dict, Any, List
from app.core.auth.auth_dependency import get_current_user, get_current_user_id
from app.core.middleware.input_guards import validate_upload_file, get_file_processing_limits
from app.core.middleware.logging_middleware import LLMUsageTracker
from app.logger.app_logger import app_logger
import asyncio
import os
import uuid
from datetime import datetime
from app.core.data.doc_handler import DocumentHandler
from app.core.data.document_store import document_store

router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = Query(...),
    request: Request = None
):
    """
    Upload a file with comprehensive validation and optional conversation linking.
    
    This endpoint demonstrates:
    - File size and type validation
    - Centralized authentication
    - Structured logging
    - Processing strategy determination
    - Optional conversation linking
    """
    app_logger.log_info(f"[Upload] Uploading file: {file.filename}")
    try:
        # Get current user using centralized auth dependency
        user_doc = await get_current_user(request)
        user_id = user_doc["_id"]
        app_logger.log_debug(f"[Upload] Authenticated user: {user_id}")

        # Validate file upload
        app_logger.log_debug(f"[Upload] Validating file: {file.filename}, size: {file.size}")
        validation_result = validate_upload_file(file, request, user_id)
        app_logger.log_debug(f"[Upload] Validation result: {validation_result['processing_strategy']}")
        
        # Determine processing strategy
        if validation_result["processing_strategy"] == "queue":
            # Queue for background processing
            app_logger.log_info(f"[Upload] File {file.filename} queued for background processing")
            response = {
                "message": "File queued for processing",
                "file_info": validation_result,
                "processing_status": "queued"
            }

            response["conversation_linking"] = "Will be linked after processing"

            return response
        else:
            # Process immediately
            app_logger.log_debug(f"[Upload] Processing {file.filename} immediately")
            content_bytes = await file.read()
            temp_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
            app_logger.log_debug(f"[Upload] Creating temp file: {temp_filename}")

            # Persist temporarily to disk for parser compatibility
            with open(temp_filename, "wb") as f:
                f.write(content_bytes)
                app_logger.log_debug(f"[Upload] Written {len(content_bytes)} bytes to temp file")
            
            try:
                # Parse document (run in thread to avoid blocking event loop)
                app_logger.log_debug(f"[Upload] Parsing document: {temp_filename}")
                parsed_doc = await asyncio.to_thread(DocumentHandler.parse_document, temp_filename)
                app_logger.log_debug(f"[Upload] Document parsed successfully, type: {parsed_doc.doc_type}")
                
                # Build metadata
                metadata = parsed_doc.metadata or {}
                metadata.update({
                    "original_filename": file.filename,
                    "extracted_title": file.filename  # Use actual filename instead of auto-extracted title
                })
                
                # Store document and chunks
                app_logger.log_debug(f"[Upload] Storing document in database")
                document_id = await document_store.store_document(
                    filename=file.filename,
                    file_type=getattr(parsed_doc.doc_type, "value", str(parsed_doc.doc_type)),
                    file_size=len(content_bytes),
                    content=parsed_doc.content,
                    metadata=metadata
                )
                app_logger.log_info(f"[Upload] Document stored successfully with ID: {document_id}")
                
                # Prepare base response
                content_preview = (
                    parsed_doc.content[:200] + "..." if len(parsed_doc.content) > 200 else parsed_doc.content
                )
                page_count = metadata.get("pages")
                
                response = {
                    "message": "File uploaded successfully",
                    "file_info": validation_result,
                    "processing_status": "immediate",
                    "document_id": document_id,
                    "doc_type": getattr(parsed_doc.doc_type, "value", str(parsed_doc.doc_type)),
                    "content_preview": content_preview,
                    "metadata": metadata,
                    "word_count": len((parsed_doc.content or "").split()),
                    "page_count": page_count,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Link to conversation
                app_logger.log_debug(f"[Upload] Attempting to link document to conversation: {conversation_id}")
                try:
                    from app.context_store.conversation_store import ConversationManager
                    # Verify user has access to conversation
                    conversation = ConversationManager.get_conversation(conversation_id)
                    if conversation.get('user_id') == user_id:
                        success = ConversationManager.add_document_to_conversation(
                            conversation_id, document_id, 
                            {"filename": file.filename, "file_type": getattr(parsed_doc.doc_type, "value", str(parsed_doc.doc_type))},
                            user_id
                        )
                        if success:
                            app_logger.log_info(f"[Upload] Document {document_id} successfully linked to conversation {conversation_id}")
                            response["conversation_linking"] = {
                                "status": "success",
                                "conversation_id": conversation_id,
                                "message": "Document linked to conversation"
                            }
                        else:
                            app_logger.log_warning(f"[Upload] Failed to link document {document_id} to conversation {conversation_id}")
                            response["conversation_linking"] = {
                                "status": "failed",
                                "message": "Document may already exist in conversation"
                            }
                    else:
                        app_logger.log_warning(f"[Upload] Access denied to conversation {conversation_id} for user {user_id}")
                        response["conversation_linking"] = {
                            "status": "failed",
                            "message": "Access denied to conversation"
                        }
                except FileNotFoundError:
                    app_logger.log_warning(f"[Upload] Conversation {conversation_id} not found")
                    response["conversation_linking"] = {
                        "status": "failed",
                        "message": "Conversation not found"
                    }
                except Exception as e:
                    app_logger.log_error(f"[Upload] Error linking document to conversation: {e}")
                    response["conversation_linking"] = {
                        "status": "failed",
                        "message": f"Error linking to conversation: {str(e)}"
                    }
                
                return response
                
            finally:
                try:
                    os.remove(temp_filename)
                except Exception as rm_err:
                    app_logger.log_warning(f"[Upload] Failed to remove temp file {temp_filename}: {rm_err}")
            
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Upload] Error uploading file {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during file upload"
        )


@router.get("/limits", response_model=Dict[str, Any])
async def get_upload_limits():
    """
    Get file upload limits and allowed types.
    
    This endpoint provides client-side validation information.
    """
    app_logger.log_debug(f"[Upload] Retrieving upload limits")
    try:
        limits = get_file_processing_limits()
        app_logger.log_debug(f"[Upload] Upload limits retrieved successfully")
        return {
            "message": "Upload limits retrieved successfully",
            "limits": limits
        }
    except Exception as e:
        app_logger.log_error(f"[Upload] Error getting upload limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/upload-multiple", response_model=Dict[str, Any])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    conversation_id: str = Query(...),
    request: Request = None
):
    """
    Upload up to 8 files in a single request and process them in parallel.

    - Validates each file using central guards
    - Determines per-file processing strategy (immediate vs queue)
    - Returns a per-file result without failing the entire batch
    - Optional conversation linking for all uploaded documents
    """
    app_logger.log_info(f"[Upload] Batch uploading {len(files) if files else 0} files")
    try:
        # Authenticate once for the entire batch
        user_doc = await get_current_user(request)
        user_id = user_doc["_id"]
        app_logger.log_debug(f"[Upload] Authenticated user for batch upload: {user_id}")

        if not files or len(files) == 0:
            app_logger.log_warning(f"[Upload] No files provided in batch upload")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        if len(files) > 8:
            app_logger.log_warning(f"[Upload] Too many files in batch: {len(files)} (max 8)")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many files. Maximum allowed is 8"
            )

        # Verify conversation access once (conversation_id is now required)
        app_logger.log_debug(f"[Upload] Verifying access to conversation: {conversation_id}")
        conversation_access = None
        try:
            from app.context_store.conversation_store import ConversationManager
            conversation = ConversationManager.get_conversation(conversation_id)
            if conversation.get('user_id') == user_id:
                conversation_access = True
                app_logger.log_debug(f"[Upload] Access granted to conversation {conversation_id}")
            else:
                conversation_access = False
                app_logger.log_warning(f"[Upload] Access denied to conversation {conversation_id}")
        except FileNotFoundError:
            conversation_access = None
            app_logger.log_warning(f"[Upload] Conversation {conversation_id} not found")

        async def validate_and_plan(file: UploadFile) -> Dict[str, Any]:
            try:
                validation_result = validate_upload_file(file, request, user_id)
                processing_status = (
                    "queued" if validation_result["processing_strategy"] == "queue" else "immediate"
                )
                
                if processing_status == "queued":
                    result = {
                        "file_name": validation_result["file_name"],
                        "file_info": validation_result,
                        "processing_status": "queued",
                        "message": "File queued for processing",
                        "document_id": None
                    }
                    
                    # Add conversation linking status for queued files
                    if conversation_access is True:
                        result["conversation_linking"] = {"status": "pending", "message": "Will be linked after processing"}
                    elif conversation_access is False:
                        result["conversation_linking"] = {"status": "failed", "message": "Access denied to conversation"}
                    else:
                        result["conversation_linking"] = {"status": "failed", "message": "Conversation not found"}
                    
                    return result
                
                # Immediate processing: parse, store, and return document_id
                # Read uploaded bytes
                content_bytes = await file.read()
                temp_filename = f"temp_{uuid.uuid4().hex}_{file.filename}"
                
                # Persist temporarily to disk for parser compatibility
                with open(temp_filename, "wb") as f:
                    f.write(content_bytes)
                
                try:
                    # Parse document (run in thread to avoid blocking event loop)
                    parsed_doc = await asyncio.to_thread(DocumentHandler.parse_document, temp_filename)
                    
                    # Build metadata
                    metadata = parsed_doc.metadata or {}
                    metadata.update({
                        "original_filename": file.filename,
                        "extracted_title": file.filename  # Use actual filename instead of auto-extracted title
                    })
                    
                    # Store document and chunks
                    document_id = await document_store.store_document(
                        filename=file.filename,
                        file_type=getattr(parsed_doc.doc_type, "value", str(parsed_doc.doc_type)),
                        file_size=len(content_bytes),
                        content=parsed_doc.content,
                        metadata=metadata
                    )
                    
                    # Prepare response
                    content_preview = (
                        parsed_doc.content[:200] + "..." if len(parsed_doc.content) > 200 else parsed_doc.content
                    )
                    page_count = metadata.get("pages")
                    
                    result = {
                        "file_name": validation_result["file_name"],
                        "file_info": validation_result,
                        "processing_status": "immediate",
                        "message": "File uploaded successfully",
                        "document_id": document_id,
                        "doc_type": getattr(parsed_doc.doc_type, "value", str(parsed_doc.doc_type)),
                        "content_preview": content_preview,
                        "metadata": metadata,
                        "word_count": len((parsed_doc.content or "").split()),
                        "page_count": page_count,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Link to conversation (conversation_id is now required)
                    if conversation_access is True:
                        try:
                            success = ConversationManager.add_document_to_conversation(
                                conversation_id, document_id,
                                {"filename": file.filename, "file_type": getattr(parsed_doc.doc_type, "value", str(parsed_doc.doc_type))},
                                user_id
                            )
                            if success:
                                result["conversation_linking"] = {
                                    "status": "success",
                                    "conversation_id": conversation_id,
                                    "message": "Document linked to conversation"
                                }
                            else:
                                result["conversation_linking"] = {
                                    "status": "failed",
                                    "message": "Document may already exist in conversation"
                                }
                        except Exception as link_err:
                            result["conversation_linking"] = {
                                "status": "failed",
                                "message": f"Error linking to conversation: {str(link_err)}"
                            }
                    else:
                        if conversation_access is False:
                            result["conversation_linking"] = {"status": "failed", "message": "Access denied to conversation"}
                        else:
                            result["conversation_linking"] = {"status": "failed", "message": "Conversation not found"}
                    
                    return result
                finally:
                    try:
                        os.remove(temp_filename)
                    except Exception as rm_err:
                        app_logger.log_warning(f"[Upload] Failed to remove temp file {temp_filename}: {rm_err}")
            except HTTPException as he:
                return {
                    "file_name": getattr(file, "filename", "unknown"),
                    "processing_status": "rejected",
                    "error": he.detail
                }
            except Exception as e:
                return {
                    "file_name": getattr(file, "filename", "unknown"),
                    "processing_status": "error",
                    "error": str(e)
                }

        app_logger.log_debug(f"[Upload] Processing {len(files)} files in parallel")
        results = await asyncio.gather(*(validate_and_plan(f) for f in files))
        app_logger.log_info(f"[Upload] Batch upload completed: {len([r for r in results if 'file_info' in r])} successful")

        summary = {
            "total": len(files),
            "success": sum(1 for r in results if "file_info" in r),
            "queued": sum(1 for r in results if r.get("processing_status") == "queued"),
            "immediate": sum(1 for r in results if r.get("processing_status") == "immediate"),
            "failed": sum(1 for r in results if "error" in r)
        }
        
        # Add conversation linking summary (conversation_id is now required)
        conversation_summary = {
            "conversation_id": conversation_id,
            "linked": sum(1 for r in results if r.get("conversation_linking", {}).get("status") == "success"),
            "link_failed": sum(1 for r in results if r.get("conversation_linking", {}).get("status") == "failed"),
            "link_pending": sum(1 for r in results if r.get("conversation_linking", {}).get("status") == "pending")
        }
        summary["conversation_linking"] = conversation_summary

        return {
            "message": "Batch processed",
            "summary": summary,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Upload] Error uploading multiple files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during multi-file upload"
        )

@router.post("/llm-process", response_model=Dict[str, Any])
async def process_with_llm(
    file: UploadFile = File(...),
    request: Request = None
):
    """
    Upload and process file with LLM (demonstrates token tracking).
    
    This endpoint shows how to track LLM usage with structured logging.
    """
    app_logger.log_info(f"[Upload] Processing file {file.filename} with LLM")
    try:
        # Get current user
        user_doc = await get_current_user(request)
        user_id = user_doc["_id"]
        app_logger.log_debug(f"[Upload] Authenticated user for LLM processing: {user_id}")

        # Validate file
        validation_result = validate_upload_file(file, request, user_id)
        app_logger.log_debug(f"[Upload] File validation completed for LLM processing")
        
        # Track LLM usage
        app_logger.log_debug(f"[Upload] Starting LLM processing for {file.filename}")
        with LLMUsageTracker(request, "file_processing") as tracker:
            # Simulate LLM processing
            tracker.set_start_tokens(100)  # Start with 100 tokens
            app_logger.log_debug(f"[Upload] LLM processing started with 100 tokens")

            # Process file content (simulated)
            content = await file.read()
            processed_content = f"Processed: {content[:100]}..."
            app_logger.log_debug(f"[Upload] File content processed, length: {len(content)} bytes")

            tracker.set_end_tokens(500)  # End with 500 tokens
            app_logger.log_info(f"[Upload] LLM processing completed, tokens used: 400")
            
            return {
                "message": "File processed with LLM",
                "file_info": validation_result,
                "processed_content": processed_content,
                "tokens_used": 400
            }
            
    except HTTPException:
        raise
    except Exception as e:
        app_logger.log_error(f"[Upload] Error processing file {file.filename} with LLM: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during LLM processing"
        ) 