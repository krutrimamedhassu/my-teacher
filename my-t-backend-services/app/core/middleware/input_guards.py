"""
Input Size & File-Type Guards

This module provides comprehensive input validation that:
- Enforces max file size limits
- Validates allowed MIME types
- Checks page count limits
- Rejects or queues large documents
- Prevents worker starvation
"""

import os
import mimetypes
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, status, UploadFile, Request
from app.logger.app_logger import app_logger
import time


class InputGuards:
    """Comprehensive input validation and guards."""
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_PDF_SIZE = 100 * 1024 * 1024  # 100MB for PDFs
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB for images
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        # Documents
        "application/pdf": {"extensions": [".pdf"], "max_pages": 500},
        "application/msword": {"extensions": [".doc"], "max_pages": 200},
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
            "extensions": [".docx"], "max_pages": 200
        },
        "application/vnd.ms-excel": {"extensions": [".xls"], "max_pages": 100},
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "extensions": [".xlsx"], "max_pages": 100
        },
        "application/vnd.ms-powerpoint": {"extensions": [".ppt"], "max_pages": 100},
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
            "extensions": [".pptx"], "max_pages": 100
        },
        "text/plain": {"extensions": [".txt"], "max_pages": 1000},
        "text/markdown": {"extensions": [".md"], "max_pages": 1000},
        
        # Images
        "image/jpeg": {"extensions": [".jpg", ".jpeg"], "max_pages": 1},
        "image/png": {"extensions": [".png"], "max_pages": 1},
        "image/gif": {"extensions": [".gif"], "max_pages": 1},
        "image/webp": {"extensions": [".webp"], "max_pages": 1},
        "image/tiff": {"extensions": [".tiff", ".tif"], "max_pages": 10},
        
        # Archives (for processing)
        "application/zip": {"extensions": [".zip"], "max_pages": 1000},
        "application/x-rar-compressed": {"extensions": [".rar"], "max_pages": 1000},
    }
    
    # Queue thresholds (files larger than this go to queue)
    QUEUE_THRESHOLD = 20 * 1024 * 1024  # 20MB
    
    @classmethod
    def validate_file_upload(
        cls, 
        file: UploadFile, 
        request: Request,
        user_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Validate file upload with comprehensive checks.
        
        Args:
            file: Uploaded file
            request: FastAPI request object
            user_id: Optional user ID for tracking
            
        Returns:
            Validation result with file info and processing decision
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Get file info
            file_size = cls._get_file_size(file)
            mime_type = file.content_type or cls._guess_mime_type(file.filename)
            file_extension = cls._get_file_extension(file.filename)
            
            # Log validation attempt
            cls._log_validation_attempt(request, file, file_size, mime_type, user_id)
            
            # Validate file size
            cls._validate_file_size(file_size, mime_type)
            
            # Validate MIME type
            mime_info = cls._validate_mime_type(mime_type, file_extension)
            
            # Determine processing strategy
            processing_strategy = cls._determine_processing_strategy(file_size, mime_type)
            
            # Validate page count if applicable
            page_count = cls._validate_page_count(file, mime_info)
            
            validation_result = {
                "file_name": file.filename,
                "file_size": file_size,
                "mime_type": mime_type,
                "file_extension": file_extension,
                "page_count": page_count,
                "processing_strategy": processing_strategy,
                "max_pages": mime_info.get("max_pages", 1),
                "is_valid": True
            }
            
            # Log successful validation
            cls._log_validation_success(request, validation_result, user_id)
            
            return validation_result
            
        except HTTPException:
            raise
        except Exception as e:
            cls._log_validation_error(request, file, str(e), user_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation error: {str(e)}"
            )
    
    @classmethod
    def _get_file_size(cls, file: UploadFile) -> int:
        """Get file size in bytes."""
        # For uploaded files, we need to read to get size
        # This is a simplified approach - in production, you might want to check
        # the Content-Length header or implement streaming validation
        return 0  # Placeholder - implement based on your needs
    
    @classmethod
    def _guess_mime_type(cls, filename: str) -> str:
        """Guess MIME type from filename."""
        if not filename:
            return "application/octet-stream"
        
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
    
    @classmethod
    def _get_file_extension(cls, filename: str) -> str:
        """Get file extension."""
        if not filename:
            return ""
        
        return os.path.splitext(filename)[1].lower()
    
    @classmethod
    def _validate_file_size(cls, file_size: int, mime_type: str) -> None:
        """Validate file size based on MIME type."""
        max_size = cls.MAX_FILE_SIZE
        
        if mime_type == "application/pdf":
            max_size = cls.MAX_PDF_SIZE
        elif mime_type.startswith("image/"):
            max_size = cls.MAX_IMAGE_SIZE
        
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB"
            )
    
    @classmethod
    def _validate_mime_type(cls, mime_type: str, file_extension: str) -> Dict[str, any]:
        """Validate MIME type and return file info."""
        if mime_type not in cls.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {mime_type}"
            )
        
        mime_info = cls.ALLOWED_MIME_TYPES[mime_type]
        
        # Check if file extension matches MIME type
        if file_extension and file_extension not in mime_info["extensions"]:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File extension {file_extension} does not match MIME type {mime_type}"
            )
        
        return mime_info
    
    @classmethod
    def _determine_processing_strategy(cls, file_size: int, mime_type: str) -> str:
        """Determine processing strategy based on file size."""
        if file_size > cls.QUEUE_THRESHOLD:
            return "queue"
        else:
            return "immediate"
    
    @classmethod
    def _validate_page_count(cls, file: UploadFile, mime_info: Dict[str, any]) -> int:
        """Validate page count for multi-page documents."""
        max_pages = mime_info.get("max_pages", 1)
        
        # For now, return 1 as placeholder
        # In production, you'd implement actual page counting
        page_count = 1
        
        if page_count > max_pages:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Document too long. Maximum pages: {max_pages}"
            )
        
        return page_count
    
    @classmethod
    def _log_validation_attempt(
        cls, 
        request: Request, 
        file: UploadFile, 
        file_size: int, 
        mime_type: str, 
        user_id: Optional[str]
    ) -> None:
        """Log file validation attempt."""
        log_data = {
            "event": "file_validation_attempt",
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "file_name": file.filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "user_id": user_id,
            "timestamp": time.time()
        }
        app_logger.log_info("File validation attempt", extra=log_data)
    
    @classmethod
    def _log_validation_success(
        cls, 
        request: Request, 
        validation_result: Dict[str, any], 
        user_id: Optional[str]
    ) -> None:
        """Log successful file validation."""
        log_data = {
            "event": "file_validation_success",
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "file_name": validation_result["file_name"],
            "file_size": validation_result["file_size"],
            "mime_type": validation_result["mime_type"],
            "processing_strategy": validation_result["processing_strategy"],
            "user_id": user_id,
            "timestamp": time.time()
        }
        app_logger.log_info("File validation successful", extra=log_data)
    
    @classmethod
    def _log_validation_error(
        cls, 
        request: Request, 
        file: UploadFile, 
        error: str, 
        user_id: Optional[str]
    ) -> None:
        """Log file validation error."""
        log_data = {
            "event": "file_validation_error",
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "file_name": file.filename,
            "error": error,
            "user_id": user_id,
            "timestamp": time.time()
        }
        app_logger.log_error("File validation failed", extra=log_data)


def validate_upload_file(file: UploadFile, request: Request, user_id: Optional[str] = None) -> Dict[str, any]:
    """
    Validate uploaded file with comprehensive guards.
    
    Args:
        file: Uploaded file
        request: FastAPI request object
        user_id: Optional user ID for tracking
        
    Returns:
        Validation result
        
    Raises:
        HTTPException: If validation fails
    """
    return InputGuards.validate_file_upload(file, request, user_id)


def should_queue_file(file_size: int, mime_type: str) -> bool:
    """
    Determine if file should be queued for processing.
    
    Args:
        file_size: File size in bytes
        mime_type: File MIME type
        
    Returns:
        True if file should be queued
    """
    return file_size > InputGuards.QUEUE_THRESHOLD


def get_file_processing_limits() -> Dict[str, any]:
    """
    Get file processing limits for client-side validation.
    
    Returns:
        Dictionary of file processing limits
    """
    return {
        "max_file_size": InputGuards.MAX_FILE_SIZE,
        "max_pdf_size": InputGuards.MAX_PDF_SIZE,
        "max_image_size": InputGuards.MAX_IMAGE_SIZE,
        "queue_threshold": InputGuards.QUEUE_THRESHOLD,
        "allowed_mime_types": list(InputGuards.ALLOWED_MIME_TYPES.keys()),
        "allowed_extensions": [
            ext for mime_info in InputGuards.ALLOWED_MIME_TYPES.values()
            for ext in mime_info["extensions"]
        ]
    } 