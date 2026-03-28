# Re-export from context_store — the implementation lives in app/context_store/document_store.py
from app.context_store.document_store import DocumentStore, document_store

__all__ = ["DocumentStore", "document_store"]
