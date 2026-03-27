from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, AsyncGenerator
import json
import asyncio
from datetime import datetime

from app.core.response.generative_responder import GenerativeResponder
from app.core.auth.optional_auth import get_user_with_usage_tracking, create_limit_exceeded_response
from app.logger.app_logger import app_logger

router = APIRouter()


class StreamingRequest(BaseModel):
    """Request model for streaming chat responses."""
    input: str = Field(..., description="The user's input message to the responder.")
    conversation_id: str = Field(..., description="The conversation ID for memory context.")
    model: Optional[str] = Field(default="gpt-4o", description="The model to use for generation.")


class SimpleStreamingRequest(BaseModel):
    """Request model for simple streaming chat responses without conversation context."""
    input: str = Field(..., description="The user's input message to the responder.")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for memory context.")
    model: Optional[str] = Field(default="gpt-4o", description="The model to use for generation.")


class StreamingResponseModel(BaseModel):
    """Response model for streaming chat responses."""
    status: str = Field(..., description="Status of the response (success/error)")
    tool: str = Field(..., description="Tool used to generate the response")
    response: str = Field(..., description="The generated response text")
    duration: float = Field(..., description="Time taken to generate the response")
    input: str = Field(..., description="Original user input")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


async def generate_streaming_response(
    user_input: str,
    conversation_id: str,
    model: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generate streaming response using OpenAI's native streaming API.
    Sends immediate acknowledgment for fast perceived response time.

    Args:
        user_input: The user's input message
        conversation_id: The conversation ID for context
        model: The model to use for generation (uses env config if not specified)

    Yields:
        SSE formatted strings for real-time streaming
    """
    from app.core.config import settings
    from app.core.response.context_manager import ContextManager

    # Use streaming model from env or default model
    final_model = model or settings.STREAMING_MODEL or settings.DEFAULT_MODEL

    app_logger.log_info(f"[Streaming] Starting native streaming for conversation: {conversation_id}, model: {final_model}")

    try:
        # Send immediate acknowledgment (< 100ms)
        yield f"data: {json.dumps({'type': 'status', 'message': 'Thinking...'})}\n\n"

        async with GenerativeResponder() as responder:
            # Build context using ContextManager
            yield f"data: {json.dumps({'type': 'status', 'message': 'Loading context...'})}\n\n"

            context_manager = ContextManager()
            messages = context_manager.build_context_messages(
                user_input=user_input,
                conversation_id=conversation_id,
                max_tokens=10000
            )

            # Send status before streaming starts
            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...'})}\n\n"

            # Stream the response using native OpenAI streaming
            full_response = ""
            async for chunk in responder.generate_streaming_text(
                messages=messages,
                model=final_model
            ):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({
                'type': 'complete',
                'response': full_response,
                'status': 'success'
            })}\n\n"

            app_logger.log_info(f"[Streaming] Completed native streaming for conversation: {conversation_id}")

    except Exception as e:
        app_logger.log_error(f"[Streaming] Error in generate_streaming_response: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate response'})}\n\n"


@router.post(
    "/chat",
    summary="Streaming Chat Response",
    description="Get a streaming response from the AI teacher using Server-Sent Events (SSE)."
)
async def stream_chat_response(request: StreamingRequest, http_request: Request) -> StreamingResponse:
    """
    Stream chat responses using Server-Sent Events (SSE).
    This endpoint provides real-time typing indicators and incremental response updates.
    Supports both authenticated and unauthenticated users with usage tracking.
    """
    try:
        # Authenticate and track usage
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "streaming"
        )
        
        app_logger.log_info(f"[Streaming] Received streaming request from {identifier}: {request.input[:50]}...")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=limit_response,
                headers=response_headers
            )
        
        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events for the streaming response."""
            try:
                # Send usage info for unauthenticated users
                if usage_info.get("tier") == "unauth":
                    remaining = usage_info.get("remaining", 0)
                    yield f"data: {json.dumps({
                        'type': 'usage_info', 
                        'remaining_requests': remaining,
                        'tier': 'unauth',
                        'message': f'You have {remaining} requests remaining as an anonymous user.'
                    })}\n\n"
                    
                    if remaining <= 2:
                        yield f"data: {json.dumps({
                            'type': 'usage_warning',
                            'message': f'Only {remaining} requests left! Create a free account for 100 requests per month.',
                            'upgrade_prompt': 'Sign up for free to continue using our AI assistant.'
                        })}\n\n"
                
                async for chunk in generate_streaming_response(
                    user_input=request.input,
                    conversation_id=request.conversation_id,
                    model=request.model
                ):
                    yield chunk
                    
            except Exception as e:
                app_logger.log_error(f"[Streaming] Error in event generator: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        # Merge response headers with SSE headers
        sse_headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
        sse_headers.update(response_headers)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers=sse_headers
        )
        
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e


@router.post(
    "/chat/simple",
    summary="Simple Streaming Chat Response",
    description="Get a simple streaming response without conversation context."
)
async def stream_simple_chat_response(request: SimpleStreamingRequest, http_request: Request) -> StreamingResponse:
    """
    Stream simple chat responses without conversation context.
    Useful for quick responses or when conversation history isn't needed.
    Supports both authenticated and unauthenticated users with usage tracking.
    """
    try:
        # Authenticate and track usage
        user_id, identifier, usage_info, response_headers = await get_user_with_usage_tracking(
            http_request, "streaming_simple"
        )
        
        app_logger.log_info(f"[Streaming] Received simple streaming request from {identifier}: {request.input[:50]}...")
        
        # Check if usage is allowed
        if not usage_info.get("allowed", False):
            limit_response = create_limit_exceeded_response(usage_info)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=limit_response,
                headers=response_headers
            )
        
        async def simple_event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events for simple streaming response."""
            from app.core.response.context_manager import ContextManager
            from app.core.config import settings

            # Use streaming model from env or default model
            final_model = request.model or settings.STREAMING_MODEL or settings.DEFAULT_MODEL

            try:
                # Send immediate acknowledgment
                yield f"data: {json.dumps({'type': 'status', 'message': 'Thinking...'})}\n\n"

                # Send usage info for unauthenticated users
                if usage_info.get("tier") == "unauth":
                    remaining = usage_info.get("remaining", 0)
                    yield f"data: {json.dumps({
                        'type': 'usage_info',
                        'remaining_requests': remaining,
                        'tier': 'unauth'
                    })}\n\n"

                async with GenerativeResponder() as responder:
                    # Build context using ContextManager
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Loading context...'})}\n\n"

                    context_manager = ContextManager()
                    messages = context_manager.build_context_messages(
                        user_input=request.input,
                        conversation_id=request.conversation_id,
                        max_tokens=10000
                    )

                    # Send status before streaming starts
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Generating response...'})}\n\n"

                    # Stream the response using native OpenAI streaming
                    full_response = ""
                    async for chunk in responder.generate_streaming_text(
                        messages=messages,
                        model=final_model
                    ):
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

                    # Send completion signal with full metadata
                    completion_data = {
                        'type': 'complete',
                        'response': full_response,
                        'status': 'success'
                    }

                    # Add usage warning for unauthenticated users
                    if usage_info.get("tier") == "unauth":
                        remaining = usage_info.get("remaining", 0)
                        if remaining <= 2:
                            completion_data['usage_warning'] = {
                                "remaining_requests": remaining,
                                "message": f"You have {remaining} requests remaining. Create a free account for 100 requests per month!",
                                "upgrade_prompt": "Sign up for free to continue using our AI assistant."
                            }

                    yield f"data: {json.dumps(completion_data)}\n\n"

            except Exception as e:
                app_logger.log_error(f"[Streaming] Error in simple event generator: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate response'})}\n\n"
        
        # Merge response headers with SSE headers
        sse_headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
        sse_headers.update(response_headers)
        
        return StreamingResponse(
            simple_event_generator(),
            media_type="text/event-stream",
            headers=sse_headers
        )
        
    except HTTPException as e:
        if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=response_headers if 'response_headers' in locals() else {}
            )
        raise e 