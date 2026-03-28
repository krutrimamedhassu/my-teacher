"""
Shared MongoDB connection for the entire application.
All stores (user, document, conversation) use this single client
instead of each opening their own connection.
"""
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from app.core.config import settings
from app.logger.app_logger import app_logger

_client: MongoClient = None


def get_client() -> MongoClient:
    """Return the shared MongoDB client, creating it on first call."""
    global _client
    if _client is None:
        app_logger.log_info("[MongoClient] Initializing shared MongoDB connection")
        uri_preview = settings.MONGODB_URI.split('@')[-1] if '@' in settings.MONGODB_URI else settings.MONGODB_URI[:50]
        app_logger.log_debug(f"[MongoClient] Connecting to: {uri_preview}")
        _client = MongoClient(settings.MONGODB_URI, server_api=ServerApi('1'))
        _client.admin.command('ping')
        app_logger.log_info("[MongoClient] Connected to MongoDB")
    return _client


def get_db():
    """Return the application database."""
    db_name = settings.MONGODB_TEST_DB or "myteacher_dev"
    return get_client()[db_name]
