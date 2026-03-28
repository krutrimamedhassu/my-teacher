import time
from typing import Dict, List, Optional, Any
from app.logger.app_logger import app_logger
from app.core.prompts import PROMPT_REGISTRY


def estimate_token_count(messages: List[Dict[str, str]]) -> int:
    """
    Estimate token count for a list of messages. Uses word count * 1.3 as a rough estimate.

    Args:
        messages: List of message dictionaries

    Returns:
        Estimated token count
    """
    total = 0
    for msg in messages:
        text = msg.get('text') or msg.get('content') or ''
        total += int(len(text.split()) * 1.3)
    return total


def trim_messages_to_token_limit(messages: List[Dict[str, str]], max_tokens: int = 10000) -> List[Dict[str, str]]:
    """
    Return the most recent messages that fit within max_tokens.

    Args:
        messages: List of message dictionaries
        max_tokens: Maximum token limit

    Returns:
        Trimmed list of messages
    """
    selected = []
    total_tokens = 0
    for msg in reversed(messages):
        tokens = estimate_token_count([msg])
        if total_tokens + tokens > max_tokens:
            break
        selected.insert(0, msg)
        total_tokens += tokens
    return selected


def estimate_token_count_simple(text: str) -> int:
    """Simple token estimation based on word count."""
    return int(len(text.split()) * 1.3)


def trim(messages: List[Dict[str, str]], limit: int = 10_000) -> List[Dict[str, str]]:
    """Keep the newest messages that still fit inside the limit."""
    sel, total = [], 0
    for m in reversed(messages):
        t = estimate_token_count_simple(m["content"])
        if total + t > limit:
            break
        sel.insert(0, m)
        total += t
    return sel


class ContextManager:
    """
    Manages conversation context and message history.
    Handles conversation memory, token limits, and message formatting.
    """
    
    def __init__(self):
        pass
    
    def build_context_messages(
        self,
        user_input: str,
        conversation_id: Optional[str] = None,
        max_tokens: int = 10000
    ) -> List[Dict[str, str]]:
        """
        Build context messages for LLM including system prompt and conversation history.

        Args:
            user_input: Current user input
            conversation_id: Optional conversation ID for history
            max_tokens: Maximum tokens to include from history

        Returns:
            List of formatted messages for OpenAI API
        """
        app_logger.log_info(f"[ContextManager] ===== BUILDING CONTEXT MESSAGES ======")
        app_logger.log_info(f"[ContextManager] Building context for input: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}'")
        app_logger.log_debug(f"[ContextManager] Conversation ID: {conversation_id}")
        app_logger.log_debug(f"[ContextManager] Max tokens limit: {max_tokens}")
        
        # Get system prompt
        app_logger.log_debug(f"[ContextManager] Loading system prompt: 'bramha'")
        teacher_prompt = PROMPT_REGISTRY["bramha"]
        app_logger.log_debug(f"[ContextManager] System prompt loaded, length: {len(teacher_prompt)} characters")

        # Base messages with system prompt and current user input
        messages = [
            {"role": "system", "content": teacher_prompt},
            {"role": "user", "content": user_input}
        ]
        app_logger.log_debug(f"[ContextManager] Base messages created: system + user input")
        
        # Add conversation history if available
        if conversation_id:
            app_logger.log_info(f"[ContextManager] ===== LOADING CONVERSATION HISTORY ======")
            try:
                history_start = time.time()
                history_messages = self._get_conversation_history(conversation_id)
                history_duration = time.time() - history_start

                if history_messages:
                    app_logger.log_info(f"[ContextManager] Loaded {len(history_messages)} history messages in {history_duration:.2f}s")

                    # Insert history between system prompt and current user input
                    all_messages = [{"role": "system", "content": teacher_prompt}] + history_messages + [{"role": "user", "content": user_input}]
                    app_logger.log_debug(f"[ContextManager] Total messages before trimming: {len(all_messages)}")

                    # Estimate tokens before trimming
                    pre_trim_tokens = estimate_token_count(all_messages)
                    app_logger.log_debug(f"[ContextManager] Estimated tokens before trim: {pre_trim_tokens}")

                    messages = trim(all_messages, limit=max_tokens)
                    post_trim_tokens = estimate_token_count(messages)
                    app_logger.log_info(f"[ContextManager] Added conversation history - Messages: {len(messages)}, Tokens: {post_trim_tokens}/{max_tokens}")

                    if len(messages) < len(all_messages):
                        app_logger.log_info(f"[ContextManager] Trimmed {len(all_messages) - len(messages)} messages due to token limit")
                else:
                    app_logger.log_info(f"[ContextManager] No conversation history found in {history_duration:.2f}s")
            except Exception as e:
                app_logger.log_error(f"[ContextManager] Error loading conversation history: {e}")
                app_logger.log_debug(f"[ContextManager] Falling back to basic messages without history")
        else:
            app_logger.log_info(f"[ContextManager] No conversation ID provided - using basic context")
        
        app_logger.log_info(f"[ContextManager] ===== CONTEXT BUILDING COMPLETE ======")
        app_logger.log_info(f"[ContextManager] Final context - Messages: {len(messages)}, Estimated tokens: {estimate_token_count(messages)}")
        app_logger.log_debug(f"[ContextManager] Message roles: {[msg.get('role') for msg in messages]}")
        app_logger.log_debug(f"[ContextManager] Message lengths: {[len(msg.get('content', '')) for msg in messages]}")

        return messages
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for OpenAI API.

        Args:
            conversation_id: Conversation ID to retrieve history for

        Returns:
            List of formatted messages
        """
        app_logger.log_debug(f"[ContextManager] Retrieving conversation history for: {conversation_id}")
        try:
            from app.context_store.conversation_store import ConversationManager
            conv = ConversationManager.get_conversation(conversation_id)
            history = conv.get("messages", [])

            app_logger.log_info(f"[ContextManager] Found {len(history)} raw messages in conversation history")
            app_logger.log_debug(f"[ContextManager] Raw message roles: {[msg.get('role') for msg in history]}")
            
            # Convert to OpenAI format: {role, content}
            formatted_messages = []
            for i, msg in enumerate(history):
                role = msg.get("role", "user")
                content = msg.get("text", "")
                formatted_messages.append({
                    "role": role,
                    "content": content
                })
                app_logger.log_debug(f"[ContextManager] Message {i+1}: {role} ({len(content)} chars)")

            app_logger.log_info(f"[ContextManager] Formatted {len(formatted_messages)} messages for OpenAI API")
            return formatted_messages
            
        except Exception as e:
            app_logger.log_error(f"[ContextManager] Error retrieving conversation history: {e}")
            return []
    
    def get_conversation_context_string(
        self, 
        conversation_id: str, 
        message_count: int = 5
    ) -> Optional[str]:
        """
        Get conversation context as a formatted string for tool usage.
        
        Args:
            conversation_id: Conversation ID to get context from
            message_count: Number of recent messages to include
            
        Returns:
            Formatted context string or None if no context available
        """
        try:
            from app.context_store.conversation_store import ConversationManager
            conv = ConversationManager.get_conversation(conversation_id)
            messages = conv.get('messages', [])
            
            if not messages:
                return None
            
            recent_messages = messages[-message_count:]
            context_parts = []
            
            for msg in recent_messages:
                role = msg.get("role", "user")
                text = msg.get("text", "")
                if role == "user":
                    context_parts.append(f"User: {text}")
                elif role == "assistant":
                    context_parts.append(f"Assistant: {text}")
            
            if context_parts:
                app_logger.log_info(f"[ContextManager] Generated context string with {len(context_parts)} messages")
                return "\n".join(context_parts)
            
        except Exception as e:
            app_logger.log_error(f"[ContextManager] Error generating context string: {e}")
        
        return None
    
    def get_conversation_content(
        self, 
        conversation_id: str, 
        message_count: int = 5
    ) -> Optional[str]:
        """
        Get conversation content formatted for content-based tools.
        
        Args:
            conversation_id: Conversation ID to extract content from
            message_count: Number of recent messages to include
            
        Returns:
            Formatted content string or None if no content available
        """
        try:
            from app.context_store.conversation_store import ConversationManager
            conv = ConversationManager.get_conversation(conversation_id)
            messages = conv.get('messages', [])
            
            if not messages:
                return None
            
            recent_messages = messages[-message_count:]
            content_parts = []
            
            for msg in recent_messages:
                role = msg.get("role", "user")
                text = msg.get("text", "")
                if role == "user":
                    content_parts.append(f"User: {text}")
                elif role == "assistant":
                    content_parts.append(f"Assistant: {text}")
            
            if content_parts:
                app_logger.log_info(f"[ContextManager] Generated content string with {len(content_parts)} messages")
                return "\n\n".join(content_parts)
            
        except Exception as e:
            app_logger.log_error(f"[ContextManager] Error generating content string: {e}")
        
        return None
    
    def validate_context_size(self, messages: List[Dict[str, str]], max_tokens: int) -> bool:
        """
        Validate that messages fit within token limit.
        
        Args:
            messages: List of messages to validate
            max_tokens: Maximum allowed tokens
            
        Returns:
            True if messages fit within limit, False otherwise
        """
        total_tokens = estimate_token_count(messages)
        fits_limit = total_tokens <= max_tokens
        
        app_logger.log_debug(f"[ContextManager] Context validation - Tokens: {total_tokens}, Limit: {max_tokens}, Fits: {fits_limit}")
        
        return fits_limit
    
    def optimize_context_for_model(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo"
    ) -> List[Dict[str, str]]:
        """
        Optimize context based on model capabilities.
        
        Args:
            messages: Messages to optimize
            model: Model name to optimize for
            
        Returns:
            Optimized messages list
        """
        # Model-specific token limits
        model_limits = {
            "gpt-3.5-turbo": 16000,
            "gpt-4": 8000,
            "gpt-4-turbo": 128000,
            "gpt-4o": 128000,
        }
        
        # Use conservative limit if model not recognized
        max_tokens = model_limits.get(model, 8000)
        
        # Reserve tokens for response (typically 1000-2000)
        context_limit = max_tokens - 2000
        
        app_logger.log_debug(f"[ContextManager] Optimizing context for {model} - Limit: {context_limit}")
        
        return trim(messages, limit=context_limit)