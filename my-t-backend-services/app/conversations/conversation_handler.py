# Re-export from context_store — the implementation lives in app/context_store/conversation_store.py
from app.context_store.conversation_store import ConversationManager

__all__ = ["ConversationManager"]
