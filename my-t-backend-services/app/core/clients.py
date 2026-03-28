import openai
from app.core.config import settings
from app.logger.app_logger import app_logger
from app.context_store.mongo_client import get_client as _get_mongo_client


class MongoDBClient:
    """Thin wrapper kept for backward compatibility. Use app.context_store.mongo_client directly."""
    def __init__(self, uri: str = None):
        self.client = _get_mongo_client()


# # Instantiate the SerpAPI client with the API key from settings
# serpapi_client = serpapi.Client(api_key=settings.SERPAPI_KEY)


class LogfireClient:
    """Centralized Logfire configuration and instrumentation."""

    def __init__(self):
        self.logfire = None
        self.is_configured = False

    def configure_logfire(self):
        """Configure Logfire if token is available."""
        if not settings.LOGFIRE_TOKEN:
            app_logger.log_info("[Clients] No Logfire token found, skipping configuration")
            return False

        try:
            import logfire
            self.logfire = logfire
            logfire.configure(token=settings.LOGFIRE_TOKEN)
            self.is_configured = True
            app_logger.log_info("[Clients] Logfire configured successfully")
            return True
        except ImportError:
            app_logger.log_warning("[Clients] Logfire not installed, skipping configuration")
            return False
        except Exception as e:
            app_logger.log_error(f"[Clients] Failed to configure Logfire: {e}")
            return False

    def instrument_fastapi(self, app):
        """Instrument FastAPI app with Logfire if configured."""
        if not self.is_configured or not self.logfire:
            return False

        try:
            self.logfire.instrument_fastapi(app, capture_headers=True)
            app_logger.log_info("[Clients] FastAPI instrumented with Logfire successfully")
            return True
        except Exception as e:
            app_logger.log_error(f"[Clients] Failed to instrument FastAPI with Logfire: {e}")
            return False


# Initialize Logfire client
logfire_client = LogfireClient()

# Instantiate the OpenAI client with the API key from settings
try:
    app_logger.log_info("[Clients] Initializing OpenAI client")
    openai_client = openai.Client(api_key=settings.OPENAI_API_KEY)
    app_logger.log_info("[Clients] OpenAI client initialized successfully")
except Exception as e:
    app_logger.log_error(f"[Clients] Failed to initialize OpenAI client: {e}")
    openai_client = None

# Instantiate the AsyncOpenAI client for async operations
try:
    app_logger.log_info("[Clients] Initializing AsyncOpenAI client")
    async_openai_client = openai.AsyncClient(api_key=settings.OPENAI_API_KEY)
    app_logger.log_info("[Clients] AsyncOpenAI client initialized successfully")
except Exception as e:
    app_logger.log_error(f"[Clients] Failed to initialize AsyncOpenAI client: {e}")
    async_openai_client = None 