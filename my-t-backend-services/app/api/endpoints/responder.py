# app/api/endpoints/responder.py
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time
from datetime import datetime

from app.core.response.generative_responder import GenerativeResponder
from app.core.auth.optional_auth import get_user_with_usage_tracking, create_limit_exceeded_response
from app.logger.app_logger import app_logger

router = APIRouter()


class ResponderRequest(BaseModel):
    """Request model for the main responder."""
    input: str = Field(..., description="The user's input message to the responder.")
    conversation_id: str = Field(..., description="The conversation ID for memory context.")


class ResponderResponse(BaseModel):
    """Response model for the main responder."""
    status: str = Field(..., description="Status of the response (success/error)")
    tool: str = Field(..., description="Tool used to generate the response")
    response: str = Field(..., description="The generated response text")
    duration: float = Field(..., description="Time taken to generate the response")
    input: str = Field(..., description="Original user input")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


@router.post(
    "/",
    response_model=ResponderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a Response from the AI Teacher",
    description=(
        "This endpoint acts as the main conversational interface. "
        "It analyzes the user's input and decides whether to use a specialized tool "
        "or generate a direct answer from the AI teacher."
    ),
)
async def get_teacher_response(request: ResponderRequest, http_request: Request) -> JSONResponse:
    """
    Processes the user's input through the generative responder to get
    an appropriate tool-based or conversational response.
    
    Supports both authenticated and unauthenticated users with usage tracking.
    """
    try:
        # Authenticate and track usage
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "responder"
        )
        
        app_logger.log_info(f"[Responder] Received input from {identifier}: {request.input!r}")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=limit_response,
                headers=response_headers
            )
        
        # Log usage info for unauthenticated users
        if usage_info.get("tier") == "unauth":
            remaining = usage_info.get("remaining", 0)
            app_logger.log_info(f"[Responder] Unauth user has {remaining} requests remaining")
        
        # Use async context manager to ensure proper cleanup
        async with GenerativeResponder() as responder:
            result = await responder.responder(request.input, request.conversation_id)
            
            # Ensure response is always a string
            response_text = result.get("response")
            if response_text is None:
                response_text = "I encountered an error while processing your request. Please try again."
            
            response_data = ResponderResponse(
                status=result.get("status"),
                tool=result.get("tool"),
                response=response_text,
                duration=result.get("duration", 0.0),
                input=request.input,
                metadata=result.get("metadata", {})
            )
            
            # Add usage information to response for unauthenticated users
            if usage_info.get("tier") == "unauth":
                remaining = usage_info.get("remaining", 0)
                if remaining <= 2:  # Show warning when only 2 requests left
                    response_data.metadata.update({
                        "usage_warning": {
                            "remaining_requests": remaining,
                            "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                            "upgrade_prompt": "Sign up for free to continue using our AI assistant."
                        }
                    })
            
            return JSONResponse(
                content=response_data.dict(),
                status_code=status.HTTP_200_OK,
                headers=response_headers
            )
            
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e
    except Exception as e:
        app_logger.log_error(f"[Responder] Error processing request: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "message": "Failed to process your request"}
        ) 