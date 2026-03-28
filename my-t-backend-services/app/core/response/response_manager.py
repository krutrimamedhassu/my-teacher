import time
import json
import os
import aiohttp
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.tools.tool_registry import ToolRegistry
from app.logger.app_logger import app_logger


async def _post_json(url: str, payload: Dict[str, Any]) -> str:
    """Make HTTP POST request with JSON payload."""
    app_logger.log_debug(f"[HTTP] Making POST request to {url}")
    app_logger.log_debug(f"[HTTP] Request payload: {payload}")

    start_time = time.monotonic()
    
    # Add internal call header to prevent double usage tracking
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Call": "true"
    }
    
    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=payload, headers=headers) as r:
            duration = time.monotonic() - start_time
            app_logger.log_info(f"[HTTP] Response received - Status: {r.status}, Duration: {duration:.2f}s")

            if r.status >= 400:
                error_text = await r.text()
                app_logger.log_error(f"[HTTP] Error response: {error_text}")
            r.raise_for_status()

            response_text = await r.text()
            app_logger.log_debug(f"[HTTP] Response text length: {len(response_text)}")

            # Try to parse as JSON and extract the explanation field if it exists
            try:
                response_json = json.loads(response_text)
                app_logger.log_debug(f"[HTTP] Parsed JSON response: {list(response_json.keys()) if isinstance(response_json, dict) else 'not a dict'}")

                if isinstance(response_json, dict) and "explanation" in response_json:
                    app_logger.log_debug(f"[HTTP] Extracting 'explanation' field")
                    return response_json["explanation"]
                elif isinstance(response_json, dict) and "answer" in response_json:
                    app_logger.log_debug(f"[HTTP] Extracting 'answer' field")
                    return response_json["answer"]
                else:
                    app_logger.log_debug(f"[HTTP] Returning full response text")
                    return response_text
            except json.JSONDecodeError as e:
                app_logger.log_warning(f"[HTTP] Failed to parse JSON response: {e}")
                return response_text


async def _post_json_with_context(url: str, payload: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> str:
    """Make HTTP POST request with JSON payload and user context for internal calls."""
    app_logger.log_debug(f"[HTTP Internal] Making POST request to {url}")
    app_logger.log_debug(f"[HTTP Internal] Request payload: {payload}")

    start_time = time.monotonic()
    
    # Add internal call header and user context headers to prevent double usage tracking
    headers = {
        "Content-Type": "application/json",
        "X-Internal-Call": "true"
    }
    
    # Propagate user context if available
    if user_context:
        if user_context.get("api_key"):
            headers["Authorization"] = f"Bearer {user_context['api_key']}"
        elif user_context.get("session_id"):
            headers["X-Session-Id"] = user_context["session_id"]
        # Add any JWT token if available
        if user_context.get("jwt_token"):
            headers["Authorization"] = f"Bearer {user_context['jwt_token']}"
    
    async with aiohttp.ClientSession() as sess:
        async with sess.post(url, json=payload, headers=headers) as r:
            duration = time.monotonic() - start_time
            app_logger.log_info(f"[HTTP Internal] Response received - Status: {r.status}, Duration: {duration:.2f}s")

            if r.status >= 400:
                error_text = await r.text()
                app_logger.log_error(f"[HTTP Internal] Error response: {error_text}")
            r.raise_for_status()

            response_text = await r.text()
            app_logger.log_debug(f"[HTTP Internal] Response text length: {len(response_text)}")

            # Try to parse as JSON and extract the relevant field
            try:
                response_json = json.loads(response_text)
                app_logger.log_debug(f"[HTTP Internal] Parsed JSON response: {list(response_json.keys()) if isinstance(response_json, dict) else 'not a dict'}")

                if isinstance(response_json, dict) and "answer" in response_json:
                    app_logger.log_debug(f"[HTTP Internal] Extracting 'answer' field")
                    return response_json["answer"]
                else:
                    app_logger.log_debug(f"[HTTP Internal] Using full response as text")
                    return response_text
            except json.JSONDecodeError:
                app_logger.log_debug(f"[HTTP Internal] Response is not JSON, returning as text")
                return response_text


class ResponseManager:
    """
    Manages response generation and tool execution.
    Handles the decision-making and execution flow for user requests.
    """
    
    def __init__(self, client: AsyncOpenAI):
        self.client = client
        self.tool_registry = ToolRegistry()
    
    async def process_request(
        self,
        messages: List[Dict[str, str]],
        user_input: str,
        conversation_id: Optional[str] = None,
        model: str = settings.DEFAULT_MODEL
    ) -> Dict[str, Any]:
        """
        Process a user request and return appropriate response.
        
        Args:
            messages: Formatted messages for LLM
            user_input: Original user input
            conversation_id: Optional conversation ID for context
            model: Model to use for generation
            
        Returns:
            Response dictionary with status, tool, response, duration, etc.
        """
        t0 = time.monotonic()
        metadata: Dict[str, Any] = {}
        
        # Extract days from user input for study planning
        from app.core.response.generative_responder import extract_days_from_text
        requested_days = extract_days_from_text(user_input)
        
        app_logger.log_info(f"[ResponseManager] ===== ENTERING RESPONSE MANAGER ======")
        app_logger.log_info(f"[ResponseManager] Processing request with {len(self.tool_registry.get_all_tools())} available tools")

        # Log tool payload details
        tools_payload = self.tool_registry.get_tools_payload()
        app_logger.log_info(f"[ResponseManager] Tools being sent to OpenAI: {[tool['function']['name'] for tool in tools_payload]}")
        app_logger.log_debug(f"[ResponseManager] Full tools payload: {len(str(tools_payload))} characters")

        try:
            # Call OpenAI with available tools
            app_logger.log_info(f"[ResponseManager] ===== CALLING OPENAI API ======")
            app_logger.log_debug(f"[ResponseManager] API call parameters - Model: {model}, Temperature: 0.3, Max tokens: 800, Tool choice: auto")
            openai_start = time.monotonic()
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=self.tool_registry.get_tools_payload(),
                tool_choice="auto",
                temperature=0.3,
                max_tokens=800,
            )
            openai_duration = time.monotonic() - openai_start
            choice = response.choices[0]
            app_logger.log_info(f"[ResponseManager] OpenAI API call completed in {openai_duration:.2f}s")
            app_logger.log_info(f"[ResponseManager] OpenAI response - Finish reason: {choice.finish_reason}")
            app_logger.log_debug(f"[ResponseManager] Response usage: {response.usage if hasattr(response, 'usage') else 'N/A'}")
            
        except Exception as e:
            app_logger.log_error(f"[ResponseManager] OpenAI call failed: {e}")
            return self._error_response("OpenAI call failed", str(e), user_input, time.monotonic() - t0)
        
        # Check if GPT called a tool
        if choice.finish_reason == "tool_calls":
            app_logger.log_info(f"[ResponseManager] ===== TOOL CALL DETECTED ======")
            tool_calls = choice.message.tool_calls
            app_logger.log_info(f"[ResponseManager] Number of tool calls: {len(tool_calls)}")

            if tool_calls:
                tool_call = tool_calls[0]
                tool_name = tool_call.function.name
                app_logger.log_info(f"[ResponseManager] Tool selected by OpenAI: {tool_name}")
                app_logger.log_debug(f"[ResponseManager] Tool call ID: {tool_call.id}")
                app_logger.log_debug(f"[ResponseManager] Raw tool arguments: {tool_call.function.arguments}")

            return await self._handle_tool_call(
                choice.message.tool_calls[0],
                user_input,
                conversation_id,
                requested_days,
                t0,
                metadata
            )
        
        # Direct LLM response
        app_logger.log_info(f"[ResponseManager] ===== DIRECT LLM RESPONSE ======")
        duration = time.monotonic() - t0
        app_logger.log_info(f"[ResponseManager] No tool call - Using direct LLM response (Bramha)")
        app_logger.log_info(f"[ResponseManager] Direct LLM response - Duration: {duration:.2f}s")
        app_logger.log_debug(f"[ResponseManager] LLM response length: {len(choice.message.content or '') if choice.message.content else 0} characters")
        app_logger.log_info(f"[ResponseManager] ===== EXITING RESPONSE MANAGER ======")

        return {
            "status": "success",
            "tool": "bramha",
            "response": choice.message.content,
            "duration": duration,
            "input": user_input,
            "metadata": metadata,
        }
    
    async def _handle_tool_call(
        self,
        tool_call,
        user_input: str,
        conversation_id: Optional[str],
        requested_days: Optional[int],
        start_time: float,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a tool call from OpenAI function calling."""
        app_logger.log_info(f"[ResponseManager] ===== HANDLING TOOL CALL ======")
        tool_name = tool_call.function.name
        raw_args = tool_call.function.arguments
        args: Dict[str, Any] = json.loads(raw_args or "{}")

        app_logger.log_info(f"[ResponseManager] Processing tool call: {tool_name}")
        app_logger.log_info(f"[ResponseManager] Tool arguments received: {list(args.keys())}")
        app_logger.log_debug(f"[ResponseManager] Full tool arguments: {args}")

        # Log tool configuration
        tool_config = self.tool_registry.get_tool(tool_name)
        app_logger.log_debug(f"[ResponseManager] Tool endpoint: {tool_config.get('endpoint', 'N/A')}")
        app_logger.log_debug(f"[ResponseManager] Tool description: {tool_config.get('description', 'N/A')[:100]}...")
        
        # Note: study_plan tool removed
        
        metadata["tool_args"] = args
        
        # Process arguments based on tool type
        app_logger.log_info(f"[ResponseManager] ===== PROCESSING TOOL ARGUMENTS ======")
        processed_args_start = time.monotonic()
        args = await self._process_tool_args(tool_name, args, conversation_id)
        processed_args_duration = time.monotonic() - processed_args_start
        app_logger.log_debug(f"[ResponseManager] Tool args processing completed in {processed_args_duration:.2f}s")

        # Validate required fields
        app_logger.log_info(f"[ResponseManager] ===== VALIDATING TOOL ARGUMENTS ======")
        missing_fields = self.tool_registry.validate_tool_args(tool_name, args)
        if missing_fields:
            app_logger.log_warning(f"[ResponseManager] Missing required fields: {missing_fields}")
        else:
            app_logger.log_debug(f"[ResponseManager] All required fields present")

        # Validate important fields (no defaults policy)
        missing_important = self.tool_registry.validate_important_fields(tool_name, args)
        if missing_important:
            app_logger.log_warning(f"[ResponseManager] Missing important fields: {missing_important}")
        else:
            app_logger.log_debug(f"[ResponseManager] All important fields present")
        
        # Special validation for celebrity persona
        if tool_name == "explain_concept" and args.get("persona") == "celebrity":
            if not args.get("celebrity_name"):
                missing_fields.append("celebrity_name")
        
        all_missing = missing_fields + missing_important
        if all_missing:
            # Special handling for build_visual tool - ask user about visual type
            if tool_name == "build_visual" and "visual_type" in all_missing:
                return self._build_visual_confirmation_response(user_input, start_time, metadata)
            return self._validation_error_response(tool_name, all_missing, user_input, start_time, metadata)
        
        # Execute tool
        app_logger.log_info(f"[ResponseManager] ===== EXECUTING TOOL ======")
        is_in_process = self.tool_registry.is_in_process_tool(tool_name)
        app_logger.log_info(f"[ResponseManager] Tool execution type: {'In-process' if is_in_process else 'HTTP'}")

        if is_in_process:
            app_logger.log_info(f"[ResponseManager] Executing in-process tool: {tool_name}")
            return await self._execute_in_process_tool(tool_name, args, user_input, start_time, metadata)
        else:
            app_logger.log_info(f"[ResponseManager] Executing HTTP tool: {tool_name}")
            return await self._execute_http_tool(tool_name, args, user_input, start_time, metadata, conversation_id)
    
    async def _process_tool_args(
        self, 
        tool_name: str, 
        args: Dict[str, Any], 
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Process and enhance tool arguments based on tool requirements."""

        # Handle content tools (resolve document references)
        if tool_name in self.tool_registry.get_content_tools():
            args = await self._resolve_document_content(args)

        
        return args

    
    async def _resolve_document_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve document content from filename references."""
        if "content" not in args:
            return args
        
        content_value = args["content"]
        
        # Check if content looks like a filename
        if (content_value.endswith('.pdf') or
            content_value.endswith('.docx') or
            content_value.endswith('.txt') or
            'A_Brief_Introduction_To_AI.pdf' in content_value):
            
            app_logger.log_info(f"[ResponseManager] Resolving document content for: {content_value}")
            
            try:
                from app.core.data.document_store import document_store
                all_docs = await document_store.list_documents(limit=100)
                
                for doc in all_docs:
                    if doc["filename"] == content_value or content_value in doc["filename"]:
                        actual_content = await document_store.get_document_content(doc["_id"])
                        if actual_content:
                            args["content"] = actual_content
                            app_logger.log_info(f"[ResponseManager] Resolved document content: {doc['filename']}")
                        break
                        
            except Exception as e:
                app_logger.log_error(f"[ResponseManager] Error resolving document: {e}")
        
        return args
    
    async def _get_conversation_context(self, conversation_id: str, message_count: int) -> Optional[str]:
        """Get conversation context as formatted string."""
        try:
            from app.context_store.conversation_store import ConversationManager
            conv = ConversationManager.get_conversation(conversation_id)
            messages = conv.get('messages', [])
            
            if messages:
                recent_messages = messages[-message_count:]
                context_parts = []
                
                for msg in recent_messages:
                    if msg.get("role") == "user":
                        context_parts.append(f"User: {msg.get('text', '')}")
                    elif msg.get("role") == "assistant":
                        context_parts.append(f"Assistant: {msg.get('text', '')}")
                
                return "\n".join(context_parts) if context_parts else None
        
        except Exception as e:
            app_logger.log_error(f"[ResponseManager] Error getting conversation context: {e}")
        
        return None
    
    async def _get_conversation_content(self, conversation_id: str, message_count: int) -> Optional[str]:
        """Get conversation content for QA generation."""
        try:
            from app.context_store.conversation_store import ConversationManager
            conv = ConversationManager.get_conversation(conversation_id)
            messages = conv.get('messages', [])
            
            if messages:
                recent_messages = messages[-message_count:]
                content_parts = []
                
                for msg in recent_messages:
                    if msg.get("role") == "user":
                        content_parts.append(f"User: {msg.get('text', '')}")
                    elif msg.get("role") == "assistant":
                        content_parts.append(f"Assistant: {msg.get('text', '')}")
                
                return "\n\n".join(content_parts) if content_parts else None
        
        except Exception as e:
            app_logger.log_error(f"[ResponseManager] Error getting conversation content: {e}")
        
        return None
    
    async def _execute_in_process_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        user_input: str,
        start_time: float,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an in-process tool."""
        app_logger.log_info(f"[ResponseManager] Executing in-process tool: {tool_name}")
        
        # No in-process tools currently supported
        answer = f"Unknown in-process tool: {tool_name}"
        status = "error"
        metadata["error"] = f"No in-process tools available: {tool_name}"
        app_logger.log_error(f"[ResponseManager] Unknown in-process tool: {tool_name}")
        
        duration = time.monotonic() - start_time
        
        return {
            "status": status,
            "tool": tool_name,
            "response": answer,
            "duration": duration,
            "input": user_input,
            "metadata": metadata,
        }
    
    async def _execute_http_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        user_input: str,
        start_time: float,
        metadata: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute an HTTP-based tool."""
        app_logger.log_info(f"[ResponseManager] ===== EXECUTING HTTP TOOL: {tool_name.upper()} ======")
        tool_config = self.tool_registry.get_tool(tool_name)
        endpoint = tool_config["endpoint"]
        url = f"{settings.DOCUMENT_STORE_INVOKER_URL}{endpoint}"

        app_logger.log_info(f"[ResponseManager] Tool endpoint URL: {url}")
        app_logger.log_debug(f"[ResponseManager] Base URL: {settings.DOCUMENT_STORE_INVOKER_URL}")
        app_logger.log_debug(f"[ResponseManager] Endpoint path: {endpoint}")
        
        # Filter args to only include valid properties
        tool_properties = self.tool_registry.get_tool_properties(tool_name)
        app_logger.log_debug(f"[ResponseManager] Valid tool properties: {list(tool_properties.keys())}")
        filtered_args = {k: v for k, v in args.items() if k in tool_properties}
        app_logger.log_info(f"[ResponseManager] Filtered arguments: {list(filtered_args.keys())}")
        app_logger.log_debug(f"[ResponseManager] Arguments removed during filtering: {[k for k in args.keys() if k not in tool_properties]}")

        # For document_query tool, add conversation_id if available
        if tool_name == "document_query" and conversation_id and "conversation_id" in tool_properties:
            filtered_args["conversation_id"] = conversation_id
            app_logger.log_info(f"[ResponseManager] Added conversation_id to document_query: {conversation_id}")
        
        try:
            # Use context-aware internal call to prevent double usage tracking
            app_logger.log_info(f"[ResponseManager] Making HTTP request to tool service...")
            http_start = time.monotonic()
            answer = await _post_json_with_context(url, filtered_args, metadata.get("user_context"))
            http_duration = time.monotonic() - http_start
            status = "success"
            app_logger.log_info(f"[ResponseManager] HTTP tool request completed successfully in {http_duration:.2f}s")
            app_logger.log_info(f"[ResponseManager] Tool response length: {len(answer) if answer else 0} characters")
            app_logger.log_debug(f"[ResponseManager] Tool response preview: {answer[:200] + '...' if answer and len(answer) > 200 else answer}")

        except Exception as e:
            http_duration = time.monotonic() - http_start if 'http_start' in locals() else 0
            answer = f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your question."
            status = "error"
            metadata["error"] = str(e)
            app_logger.log_error(f"[ResponseManager] HTTP tool failed after {http_duration:.2f}s: {e}")
            app_logger.log_error(f"[ResponseManager] Error type: {type(e).__name__}")

        duration = time.monotonic() - start_time
        app_logger.log_info(f"[ResponseManager] ===== HTTP TOOL EXECUTION COMPLETE ======")
        app_logger.log_info(f"[ResponseManager] Total tool execution time: {duration:.2f}s")
        app_logger.log_info(f"[ResponseManager] Final status: {status}")

        return {
            "status": status,
            "tool": tool_name,
            "response": answer,
            "duration": duration,
            "input": user_input,
            "metadata": metadata,
        }
    
    def _error_response(self, error_type: str, error_msg: str, user_input: str, duration: float) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "status": "error",
            "tool": "error",
            "response": f"I encountered an error: {error_msg}. Please try again.",
            "duration": duration,
            "input": user_input,
            "metadata": {"error": error_msg, "error_type": error_type},
        }
    
    def _build_visual_confirmation_response(
        self,
        user_input: str,
        start_time: float,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a confirmation response for build_visual tool."""
        answer = "I can create a visual for you. We currently support flowchart. Is that ok?"

        return {
            "status": "success",
            "tool": "bramha",
            "response": answer,
            "duration": time.monotonic() - start_time,
            "input": user_input,
            "metadata": metadata,
        }

    def _validation_error_response(
        self,
        tool_name: str,
        missing_fields: List[str],
        user_input: str,
        start_time: float,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a validation error response."""
        answer = (
            f"Sorry, I couldn't process your request because the following required information was missing: {', '.join(missing_fields)}. "
            f"Please rephrase your request or provide the missing details."
        )
        metadata["error"] = f"Missing fields: {missing_fields}"

        return {
            "status": "error",
            "tool": tool_name,
            "response": answer,
            "duration": time.monotonic() - start_time,
            "input": user_input,
            "metadata": metadata,
        }