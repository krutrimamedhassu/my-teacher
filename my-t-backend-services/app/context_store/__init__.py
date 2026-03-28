"""
context_store — centralised data persistence layer.

All MongoDB and vector-related storage lives here.
Add new stores (e.g. vector_store.py) in this package.
"""
from app.context_store.mongo_client import get_client, get_db
from app.context_store.user_store import DatabaseManager, db_manager
from app.context_store.document_store import DocumentStore, document_store
from app.context_store.conversation_store import ConversationManager

__all__ = [
    "get_client",
    "get_db",
    "DatabaseManager",
    "db_manager",
    "DocumentStore",
    "document_store",
    "ConversationManager",
]
