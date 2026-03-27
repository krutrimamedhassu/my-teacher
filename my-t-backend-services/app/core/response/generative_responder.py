import re
import asyncio
import json
import requests
import time
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple, Union
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.prompts import PROMPT_REGISTRY, PromptTemplate
from app.core.tools.tool_registry import ToolRegistry
from app.core.response.response_manager import ResponseManager
from app.core.response.context_manager import ContextManager
from app.logger.app_logger import app_logger


# Helper functions moved to context_manager.py - keeping for backwards compatibility
from app.core.response.context_manager import estimate_token_count, trim_messages_to_token_limit, estimate_token_count_simple, trim




def extract_days_from_text(text: str) -> Optional[int]:
    """Extracts a number of days from phrases like 'in 12 days', 'for 7 days', etc."""
    app_logger.log_debug(f"[GenerativeResponder] Extracting days from text: '{text[:100]}{'...' if len(text) > 100 else ''}'")

    match = re.search(r'(?:in|for|over|within)\s+(\d{1,3})\s+days?', text, re.IGNORECASE)
    if match:
        days = int(match.group(1))
        app_logger.log_debug(f"[GenerativeResponder] Extracted {days} days from text")
        return days

    app_logger.log_debug(f"[GenerativeResponder] No days pattern found in text")
    return None


class GenerativeResponder:
    """
    Main LLM client for OpenAI, now refactored to use modular components.
    Handles OpenAI client management and provides high-level interface.
    """

    def __init__(self, api_key: str = settings.OPENAI_API_KEY) -> None:
        """
        Instantiate a dedicated OpenAI async client with your API key.

        Args:
            api_key: Your OpenAI API key.

        Raises:
            ValueError: If no API key is provided.
        """
        app_logger.log_info(f"[GenerativeResponder] Initializing GenerativeResponder")

        if not api_key:
            app_logger.log_error(f"[GenerativeResponder] OpenAI API key not provided")
            raise ValueError("OpenAI API key not found in settings.")

        # Sanitize API key for logging (show only first few characters)
        api_key_preview = f"{api_key[:8]}..." if len(api_key) > 8 else "[short_key]"
        app_logger.log_debug(f"[GenerativeResponder] Using API key: {api_key_preview}")

        try:
            self.client = AsyncOpenAI(api_key=api_key)
            self._closed = False
            app_logger.log_debug(f"[GenerativeResponder] OpenAI async client created successfully")

            # Initialize component managers
            app_logger.log_debug(f"[GenerativeResponder] Initializing ResponseManager and ContextManager")
            self.response_manager = ResponseManager(self.client)
            self.context_manager = ContextManager()

            app_logger.log_info(f"[GenerativeResponder] GenerativeResponder initialized successfully")
        except Exception as e:
            app_logger.log_error(f"[GenerativeResponder] Error initializing GenerativeResponder: {str(e)}")
            raise

    async def close(self) -> None:
        """
        Properly close the OpenAI client to prevent httpx connection cleanup errors.
        This should be called when the application is shutting down.
        """
        app_logger.log_info(f"[GenerativeResponder] Attempting to close OpenAI client, closed status: {self._closed}")

        if not self._closed and hasattr(self.client, 'close'):
            try:
                app_logger.log_debug(f"[GenerativeResponder] Closing OpenAI client connection")
                await self.client.close()
                app_logger.log_info("[GenerativeResponder] OpenAI client closed successfully")
            except Exception as e:
                app_logger.log_warning(f"[GenerativeResponder] Error closing OpenAI client: {str(e)}")
            finally:
                self._closed = True
                app_logger.log_debug(f"[GenerativeResponder] Client marked as closed")
        else:
            app_logger.log_debug(f"[GenerativeResponder] Client already closed or no close method available")

    async def __aenter__(self):
        """Async context manager entry."""
        app_logger.log_debug(f"[GenerativeResponder] Entering async context manager")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures proper cleanup."""
        if exc_type:
            app_logger.log_warning(f"[GenerativeResponder] Exiting context manager with exception: {exc_type.__name__}: {exc_val}")
        else:
            app_logger.log_debug(f"[GenerativeResponder] Exiting context manager normally")
        await self.close()

    async def generate_text(
        self,
        *,
        prompt_name: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = settings.DEFAULT_MODEL,
        max_tokens: int = 10000,
        temperature: float = 0.7,
        retries: int = 5,
    ) -> str:
        """
        Returns the LLM-generated text, retrying up to `retries` times on failure.
        - If `messages` is provided, uses them directly.
        - Otherwise uses `prompt_name` + `variables` to build a single user message.

        Args:
            prompt_name: Name of prompt template to use
            variables: Variables to substitute in the prompt template
            messages: Pre-formatted messages to send directly
            model: Model identifier to use
            max_tokens: Maximum tokens for completion
            temperature: Temperature parameter (0-1)
            retries: Number of retry attempts on failure

        Returns:
            Generated text content

        Raises:
            ValueError: if neither prompt_name nor messages is provided
            KeyError: if prompt_name not found in PROMPT_REGISTRY
            RuntimeError: after exhausting all retries
        """
        start_time = time.time()
        app_logger.log_info(f"[GenerativeResponder] Entering generate_text - prompt_name: {prompt_name}, model: {model}")
        app_logger.log_debug(f"[GenerativeResponder] Parameters - max_tokens: {max_tokens}, temperature: {temperature}, retries: {retries}")

        # Step 1: assemble messages
        if messages is None:
            if prompt_name is None:
                app_logger.log_error(f"[GenerativeResponder] Neither prompt_name nor messages provided")
                raise ValueError("Either `prompt_name` or `messages` must be provided.")

            app_logger.log_debug(f"[GenerativeResponder] Looking up prompt template: {prompt_name}")
            tpl = PROMPT_REGISTRY.get(prompt_name)
            if not isinstance(tpl, PromptTemplate):
                app_logger.log_error(f"[GenerativeResponder] Prompt template '{prompt_name}' not found in registry")
                raise KeyError(f"Prompt '{prompt_name}' not found in PROMPT_REGISTRY.")

            app_logger.log_debug(f"[GenerativeResponder] Rendering prompt with variables: {list(variables.keys()) if variables else 'none'}")
            rendered = tpl.format(**(variables or {}))
            messages = [{"role": "user", "content": rendered}]
            app_logger.log_debug(f"[GenerativeResponder] Prompt rendered, message length: {len(rendered)}")
        else:
            app_logger.log_debug(f"[GenerativeResponder] Using provided messages, count: {len(messages)}")

        # Log request details (sanitize message content for brevity)
        message_preview = str(messages)[:200] + "..." if len(str(messages)) > 200 else str(messages)
        app_logger.log_debug(f"[GenerativeResponder] LLM request - model: {model}, temp: {temperature}, max_tokens: {max_tokens}")
        app_logger.log_debug(f"[GenerativeResponder] Messages preview: {message_preview}")

        # Step 2: retry loop
        last_exc: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                app_logger.log_debug(f"[GenerativeResponder] Attempt {attempt}/{retries} - calling OpenAI API")
                attempt_start = time.time()

                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                attempt_duration = time.time() - attempt_start
                content = response.choices[0].message.content

                app_logger.log_info(f"[GenerativeResponder] LLM success on attempt {attempt} in {attempt_duration:.2f}s")
                app_logger.log_debug(f"[GenerativeResponder] Response length: {len(content) if content else 0} characters")
                app_logger.log_debug(f"[GenerativeResponder] Response preview: {content[:100] + '...' if content and len(content) > 100 else content}")

                total_duration = time.time() - start_time
                app_logger.log_info(f"[GenerativeResponder] generate_text completed successfully in {total_duration:.2f}s")
                return content

            except Exception as exc:
                last_exc = exc
                attempt_duration = time.time() - attempt_start if 'attempt_start' in locals() else 0
                app_logger.log_warning(f"[GenerativeResponder] Attempt {attempt}/{retries} failed after {attempt_duration:.2f}s: {type(exc).__name__}: {str(exc)}")

                if attempt < retries:
                    backoff = 2 ** (attempt - 1)
                    app_logger.log_debug(f"[GenerativeResponder] Backing off for {backoff}s before retry...")
                    await asyncio.sleep(backoff)
                else:
                    total_duration = time.time() - start_time
                    app_logger.log_error(f"[GenerativeResponder] All {retries} attempts failed after {total_duration:.2f}s")
                    raise RuntimeError(f"LLM generation failed after {retries} retries.") from last_exc

        # Should never reach here
        assert False, "Unreachable code in generate_text()"

    async def generate_streaming_text(
        self,
        *,
        prompt_name: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        model: str = settings.DEFAULT_MODEL,
        max_tokens: int = 10000,
        temperature: float = 0.7,
    ):
        """
        Stream LLM-generated text using OpenAI's native streaming API.
        Yields chunks of text as they arrive from the API.

        Args:
            prompt_name: Name of prompt template to use
            variables: Variables to substitute in the prompt template
            messages: Pre-formatted messages to send directly
            model: Model identifier to use
            max_tokens: Maximum tokens for completion
            temperature: Temperature parameter (0-1)

        Yields:
            Text chunks as they arrive from OpenAI

        Raises:
            ValueError: if neither prompt_name nor messages is provided
            KeyError: if prompt_name not found in PROMPT_REGISTRY
        """
        start_time = time.time()
        app_logger.log_info(f"[GenerativeResponder] Entering generate_streaming_text - prompt_name: {prompt_name}, model: {model}")
        app_logger.log_debug(f"[GenerativeResponder] Stream parameters - max_tokens: {max_tokens}, temperature: {temperature}")

        # Step 1: assemble messages
        if messages is None:
            if prompt_name is None:
                app_logger.log_error(f"[GenerativeResponder] Neither prompt_name nor messages provided")
                raise ValueError("Either `prompt_name` or `messages` must be provided.")

            app_logger.log_debug(f"[GenerativeResponder] Looking up prompt template: {prompt_name}")
            tpl = PROMPT_REGISTRY.get(prompt_name)
            if not isinstance(tpl, PromptTemplate):
                app_logger.log_error(f"[GenerativeResponder] Prompt template '{prompt_name}' not found in registry")
                raise KeyError(f"Prompt '{prompt_name}' not found in PROMPT_REGISTRY.")

            app_logger.log_debug(f"[GenerativeResponder] Rendering prompt with variables: {list(variables.keys()) if variables else 'none'}")
            rendered = tpl.format(**(variables or {}))
            messages = [{"role": "user", "content": rendered}]
            app_logger.log_debug(f"[GenerativeResponder] Prompt rendered, message length: {len(rendered)}")
        else:
            app_logger.log_debug(f"[GenerativeResponder] Using provided messages, count: {len(messages)}")

        message_preview = str(messages)[:200] + "..." if len(str(messages)) > 200 else str(messages)
        app_logger.log_debug(f"[GenerativeResponder] Stream request - model: {model}, temp: {temperature}, max_tokens: {max_tokens}")
        app_logger.log_debug(f"[GenerativeResponder] Messages preview: {message_preview}")

        try:
            app_logger.log_debug(f"[GenerativeResponder] Starting OpenAI streaming API call")
            stream_start = time.time()

            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            chunk_count = 0
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    chunk_count += 1
                    yield content

            stream_duration = time.time() - stream_start
            total_duration = time.time() - start_time
            app_logger.log_info(f"[GenerativeResponder] Streaming completed - {chunk_count} chunks in {stream_duration:.2f}s (total: {total_duration:.2f}s)")

        except Exception as exc:
            stream_duration = time.time() - start_time
            app_logger.log_error(f"[GenerativeResponder] Streaming failed after {stream_duration:.2f}s: {type(exc).__name__}: {str(exc)}")
            raise RuntimeError(f"LLM streaming failed: {str(exc)}") from exc

    async def generate_title(self, message: str) -> str:
        """
        Generate a short (max 4 words) conversation title for the given message using the LLM.

        Args:
            message: The message to generate a title for

        Returns:
            A short title (up to 4 words)
        """
        app_logger.log_info(f"[GenerativeResponder] Entering generate_title for message length: {len(message)}")
        app_logger.log_debug(f"[GenerativeResponder] Message preview: {message[:100] + '...' if len(message) > 100 else message}")

        try:
            prompt = (
                "Generate a short, relevant conversation title (no more than 4 words) for the following message. "
                "Respond with only the title, no punctuation, no quotes, no extra text.\n"
                f"Message: {message}"
            )
            messages = [
                {"role": "system", "content": "You are a helpful assistant that creates concise conversation titles."},
                {"role": "user", "content": prompt},
            ]

            app_logger.log_debug(f"[GenerativeResponder] Generating title with max_tokens=10, temperature=0.4")
            title = await self.generate_text(messages=messages, max_tokens=10, temperature=0.4)

            app_logger.log_debug(f"[GenerativeResponder] Raw title generated: '{title}'")

            # Post-process: take only first 4 words, strip punctuation, trim
            words = re.findall(r'\b\w+\b', title)
            processed_title = ' '.join(words[:4])

            app_logger.log_info(f"[GenerativeResponder] Title generated successfully: '{processed_title}'")
            return processed_title

        except Exception as e:
            app_logger.log_error(f"[GenerativeResponder] Error generating title: {str(e)}")
            # Return a fallback title
            fallback_title = "New Conversation"
            app_logger.log_warning(f"[GenerativeResponder] Using fallback title: '{fallback_title}'")
            return fallback_title

    async def generate_response_with_memory(
        self,
        conversation_id: str,
        user_message: str,
        role: str = "user",
        max_tokens: int = 10000,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Fetch conversation history, trim to last max_tokens, and generate a response using the LLM.
        Appends the new user message to the context.

        Args:
            conversation_id: Unique identifier for the conversation
            user_message: The new message to respond to
            role: Role of the message sender
            max_tokens: Maximum tokens to include from history
            model: Model to use for generation

        Returns:
            Generated response text
        """
        app_logger.log_info(f"[GenerativeResponder] Entering generate_response_with_memory for conversation: {conversation_id}")
        app_logger.log_debug(f"[GenerativeResponder] Message role: {role}, length: {len(user_message)}, max_tokens: {max_tokens}")
        app_logger.log_debug(f"[GenerativeResponder] Model: {model or settings.DEFAULT_MODEL}")

        try:
            from app.conversations.conversation_handler import ConversationManager

            app_logger.log_debug(f"[GenerativeResponder] Fetching conversation history for: {conversation_id}")
            conv = ConversationManager.get_conversation(conversation_id)
            messages = conv.get('messages', [])

            app_logger.log_debug(f"[GenerativeResponder] Found {len(messages)} messages in conversation history")

            # Convert to OpenAI format: {role, content}
            formatted = []
            for i, msg in enumerate(messages):
                formatted.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("text", "")
                })

            app_logger.log_debug(f"[GenerativeResponder] Formatted {len(formatted)} historical messages")

            # Add the new user message
            formatted.append({"role": role, "content": user_message})
            app_logger.log_debug(f"[GenerativeResponder] Added new message, total messages: {len(formatted)}")

            # Trim messages to token limit
            app_logger.log_debug(f"[GenerativeResponder] Trimming messages to {max_tokens} tokens")
            trimmed = trim_messages_to_token_limit(formatted, max_tokens=max_tokens)
            app_logger.log_debug(f"[GenerativeResponder] Trimmed to {len(trimmed)} messages")

            final_model = model or settings.DEFAULT_MODEL
            app_logger.log_info(f"[GenerativeResponder] Generating response with model: {final_model}")

            response = await self.generate_text(messages=trimmed, model=final_model, **kwargs)

            app_logger.log_info(f"[GenerativeResponder] Successfully generated response with memory for conversation: {conversation_id}")
            return response

        except Exception as e:
            app_logger.log_error(f"[GenerativeResponder] Error in generate_response_with_memory for conversation {conversation_id}: {str(e)}")
            raise

    async def responder(
        self,
        user_input: str,
        conversation_id: Optional[str] = None,
        model: str = settings.DEFAULT_MODEL,
    ) -> Dict[str, Any]:
        """
        Main responder method that coordinates context building and response generation.

        Args:
            user_input: User's input message
            conversation_id: Optional conversation ID for context
            model: Model to use for generation

        Returns:
            Response dictionary with status, tool, response, duration, etc.
        """
        start_time = time.time()
        input_preview = f"'{user_input[:100]}{'...' if len(user_input) > 100 else ''}'"
        app_logger.log_info(f"[GenerativeResponder] ========== ENTERING RESPONDER ===========")
        app_logger.log_info(f"[GenerativeResponder] Starting responder - Input: {input_preview}")
        app_logger.log_info(f"[GenerativeResponder] Conversation ID: {conversation_id}, Model: {model}")
        app_logger.log_debug(f"[GenerativeResponder] Input length: {len(user_input)} characters")

        # Log available tools
        available_tools = self.response_manager.tool_registry.get_all_tools()
        app_logger.log_info(f"[GenerativeResponder] Available tools: {list(available_tools.keys())}")
        app_logger.log_debug(f"[GenerativeResponder] Total tools available: {len(available_tools)}")

        try:
            # Build context messages using ContextManager
            app_logger.log_info(f"[GenerativeResponder] ===== STEP 1: BUILDING CONTEXT ======")
            app_logger.log_debug(f"[GenerativeResponder] Building context messages with ContextManager")
            context_start = time.time()
            messages = self.context_manager.build_context_messages(
                user_input=user_input,
                conversation_id=conversation_id,
                max_tokens=10000
            )
            context_duration = time.time() - context_start
            app_logger.log_info(f"[GenerativeResponder] Context built in {context_duration:.2f}s, message count: {len(messages)}")
            app_logger.log_debug(f"[GenerativeResponder] Context messages roles: {[msg.get('role') for msg in messages]}")

            # Process request using ResponseManager
            app_logger.log_info(f"[GenerativeResponder] ===== STEP 2: PROCESSING REQUEST ======")
            app_logger.log_info(f"[GenerativeResponder] Processing request with ResponseManager")
            app_logger.log_debug(f"[GenerativeResponder] Sending {len(messages)} messages to ResponseManager")
            response_start = time.time()
            result = await self.response_manager.process_request(
                messages=messages,
                user_input=user_input,
                conversation_id=conversation_id,
                model=model
            )
            response_duration = time.time() - response_start

            total_duration = time.time() - start_time
            app_logger.log_info(f"[GenerativeResponder] ===== RESPONDER COMPLETED ======")
            app_logger.log_info(f"[GenerativeResponder] Request completed successfully in {total_duration:.2f}s")
            app_logger.log_info(f"[GenerativeResponder] FINAL RESULT - Status: {result.get('status')}, Tool Used: {result.get('tool')}")
            app_logger.log_info(f"[GenerativeResponder] Response length: {len(result.get('response', '')) if result.get('response') else 0} characters")
            app_logger.log_info(f"[GenerativeResponder] Timing breakdown - Context: {context_duration:.2f}s, Response: {response_duration:.2f}s, Total: {total_duration:.2f}s")
            app_logger.log_debug(f"[GenerativeResponder] Full result metadata: {result.get('metadata', {})}")
            app_logger.log_info(f"[GenerativeResponder] ========== EXITING RESPONDER ===========\n")

            return result

        except Exception as e:
            total_duration = time.time() - start_time
            app_logger.log_error(f"[GenerativeResponder] ===== RESPONDER ERROR ======")
            app_logger.log_error(f"[GenerativeResponder] Error in responder after {total_duration:.2f}s for input {input_preview}: {str(e)}")
            app_logger.log_error(f"[GenerativeResponder] Exception type: {type(e).__name__}")
            app_logger.log_error(f"[GenerativeResponder] ========== EXITING RESPONDER WITH ERROR ===========\n")
            raise

