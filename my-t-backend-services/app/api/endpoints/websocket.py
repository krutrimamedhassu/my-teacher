from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from typing import Dict, Any, Optional, AsyncGenerator
import json
import asyncio
from datetime import datetime

from app.core.response.generative_responder import GenerativeResponder
from app.core.middleware.api_key_middleware import api_key_auth
from app.core.auth.api_key_models import UserTier, TIER_MESSAGES
from app.core.data.database import db_manager
from app.logger.app_logger import app_logger

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        app_logger.log_info(f"[WebSocket] Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            app_logger.log_info(f"[WebSocket] Client {client_id} disconnected")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                app_logger.log_error(f"[WebSocket] Error sending message to {client_id}: {e}")
                self.disconnect(client_id)


manager = ConnectionManager()


async def generate_websocket_response(
    user_input: str,
    conversation_id: Optional[str] = None,
    model: str = "gpt-4o"
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate streaming response for WebSocket connection.
    
    Args:
        user_input: The user's input message
        conversation_id: The conversation ID for context (optional)
        model: The model to use for generation
        
    Yields:
        Dictionary messages for WebSocket streaming
    """
    app_logger.log_info(f"[WebSocket] Starting streaming response for conversation: {conversation_id}")
    
    try:
        async with GenerativeResponder() as responder:
            # Use the responder to get tool detection and metadata
            result = await responder.responder(user_input, conversation_id, model)
            
            # Get the response text and tool information
            response_text = result.get("response", "")
            duration = result.get("duration", 0.0)
            metadata = result.get("metadata", {})
            tool_name = result.get("tool", "teacher")
            
            # Send tool information first
            yield {"type": "tool", "tool": tool_name, "metadata": metadata}
            
            # Send initial status
            yield {"type": "status", "message": "Starting response generation..."}
            
            # Stream the response character by character
            for char in response_text:
                yield {"type": "content", "content": char}
                # Add a small delay for more realistic typing effect
                await asyncio.sleep(0.01)
            
            # Send completion signal with full metadata
            yield {
                "type": "complete", 
                "response": response_text, 
                "duration": duration,
                "status": result.get("status", "success"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            app_logger.log_info(f"[WebSocket] Completed streaming response for conversation: {conversation_id}")
                
    except Exception as e:
        app_logger.log_error(f"[WebSocket] Error in generate_websocket_response: {e}")
        yield {"type": "error", "message": "Failed to generate response"}


async def authenticate_websocket_user(
    api_key: Optional[str] = None,
    session_id: Optional[str] = None,
    client_id: str = "unknown"
) -> tuple[Optional[str], str, Dict[str, Any]]:
    """
    Authenticate WebSocket user via query parameters.
    
    Returns:
        Tuple of (user_id_or_none, identifier, usage_info)
    """
    try:
        if api_key and api_key.startswith("sk-"):
            # API key authentication
            api_key_doc = db_manager.authenticate_api_key(api_key)
            if api_key_doc:
                user_id = api_key_doc["user_id"]
                usage_result = db_manager.track_api_usage(api_key, user_id, "websocket")
                return user_id, user_id, usage_result
            else:
                return None, "invalid_key", {"allowed": False, "reason": "invalid_api_key"}
        
        # Session-based tracking for unauthenticated users
        if not session_id:
            session_id = f"ws_{client_id}_{datetime.utcnow().timestamp()}"
        
        session_data = api_key_auth.track_unauth_usage(session_id)
        
        if session_data["count"] > 5:
            return None, session_id, {
                "allowed": False,
                "reason": "usage_limit_exceeded",
                "tier": "unauth",
                "message": TIER_MESSAGES[UserTier.UNAUTH]["limit_exceeded"]
            }
        
        return None, session_id, {
            "allowed": True,
            "session_id": session_id,
            "usage_count": session_data["count"],
            "remaining": 5 - session_data["count"],
            "tier": "unauth"
        }
        
    except Exception as e:
        app_logger.log_error(f"[WebSocket] Authentication error: {e}")
        return None, "error", {"allowed": False, "reason": "auth_error"}


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str,
    api_key: Optional[str] = Query(None, description="API key for authentication"),
    session_id: Optional[str] = Query(None, description="Session ID for anonymous users")
):
    """
    WebSocket endpoint for real-time chat communication with API key support.
    
    Authentication options:
    - api_key: API key for authenticated users (ws://host/ws/client123?api_key=sk-xxx)
    - session_id: Session ID for anonymous users (ws://host/ws/client123?session_id=uuid)
    
    Expected message format:
    {
        "type": "chat",
        "input": "user message",
        "conversation_id": "optional-conversation-id",
        "model": "gpt-4o"
    }
    """
    # Authenticate user before accepting connection
    user_id, identifier, auth_info = await authenticate_websocket_user(api_key, session_id, client_id)
    
    if not auth_info.get("allowed", False):
        # Send error and close connection
        await websocket.accept()
        error_msg = {
            "type": "auth_error",
            "message": auth_info.get("message", "Authentication failed"),
            "reason": auth_info.get("reason", "unknown"),
            "tier": auth_info.get("tier", "unauth")
        }
        await websocket.send_text(json.dumps(error_msg))
        await websocket.close(code=1008)  # Policy violation
        return
    
    await manager.connect(websocket, client_id)
    app_logger.log_info(f"[WebSocket] Client {client_id} authenticated as {identifier} ({auth_info.get('tier', 'unknown')} tier)")
    
    # Send welcome message with usage info
    welcome_msg = {
        "type": "welcome",
        "client_id": client_id,
        "tier": auth_info.get("tier", "unauth"),
        "authenticated": user_id is not None
    }
    
    if auth_info.get("tier") == "unauth":
        welcome_msg["remaining_requests"] = auth_info.get("remaining", 0)
        welcome_msg["usage_message"] = f"You have {auth_info.get('remaining', 0)} requests remaining as an anonymous user."
    
    await manager.send_personal_message(welcome_msg, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            app_logger.log_info(f"[WebSocket] Received message from {client_id}: {message.get('type', 'unknown')}")
            
            if message.get("type") == "chat":
                user_input = message.get("input", "")
                conversation_id = message.get("conversation_id")
                model = message.get("model", "gpt-4o")
                
                if not user_input:
                    await manager.send_personal_message(
                        {"type": "error", "message": "No input provided"}, 
                        client_id
                    )
                    continue
                
                # Re-check usage limits before processing (for real-time updates)
                if auth_info.get("tier") == "unauth":
                    current_session_data = api_key_auth.track_unauth_usage(identifier)
                    if current_session_data["count"] > 5:
                        await manager.send_personal_message({
                            "type": "usage_limit_exceeded",
                            "message": "You've reached the limit for anonymous users. Please login or create an account for more requests.",
                            "remaining_requests": 0,
                            "upgrade_message": "Create a free account to get 100 requests per month!"
                        }, client_id)
                        continue
                
                # Generate and stream response
                async for response_chunk in generate_websocket_response(
                    user_input=user_input,
                    conversation_id=conversation_id,
                    model=model
                ):
                    await manager.send_personal_message(response_chunk, client_id)
                    
            elif message.get("type") == "ping":
                # Handle ping for connection health
                await manager.send_personal_message({"type": "pong"}, client_id)
                
            else:
                await manager.send_personal_message(
                    {"type": "error", "message": "Unknown message type"}, 
                    client_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        app_logger.log_error(f"[WebSocket] Error in websocket_endpoint: {e}")
        manager.disconnect(client_id)


@router.websocket("/ws/chat/{conversation_id}")
async def conversation_websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint specifically for conversation-based chat.
    Automatically includes conversation context.
    
    Expected message format:
    {
        "type": "chat",
        "input": "user message",
        "model": "gpt-4o"
    }
    """
    await manager.connect(websocket, conversation_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            app_logger.log_info(f"[WebSocket] Received conversation message: {message.get('type', 'unknown')}")
            
            if message.get("type") == "chat":
                user_input = message.get("input", "")
                model = message.get("model", "gpt-4o")
                
                if not user_input:
                    await manager.send_personal_message(
                        {"type": "error", "message": "No input provided"}, 
                        conversation_id
                    )
                    continue
                
                # Generate and stream response with conversation context
                async for response_chunk in generate_websocket_response(
                    user_input=user_input,
                    conversation_id=conversation_id,
                    model=model
                ):
                    await manager.send_personal_message(response_chunk, conversation_id)
                    
            elif message.get("type") == "ping":
                # Handle ping for connection health
                await manager.send_personal_message({"type": "pong"}, conversation_id)
                
            else:
                await manager.send_personal_message(
                    {"type": "error", "message": "Unknown message type"}, 
                    conversation_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
    except Exception as e:
        app_logger.log_error(f"[WebSocket] Error in conversation_websocket_endpoint: {e}")
        manager.disconnect(conversation_id) 