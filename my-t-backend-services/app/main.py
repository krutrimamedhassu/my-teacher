import sys
import os

# Ensure the package root (my-t-backend-services/) is on sys.path regardless of
# how or from where this file is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.api_v1 import api_router
from app.core.config import settings
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from app.logger.app_logger import app_logger
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware.logging_middleware import StructuredLoggingMiddleware
from app.core.clients import logfire_client


app = FastAPI(
    title=settings.TITLE_OF_THE_PROJECT,
    description=settings.DESCRIPTION_OF_THE_PROJECT,
    version=settings.VERSION
)

# Configure and instrument Logfire
logfire_client.configure_logfire()
logfire_client.instrument_fastapi(app)

# Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

_cors_origins_env = os.getenv("BACKEND_CORS_ORIGINS", "")
_cors_origins = (
    [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
    if _cors_origins_env
    else ["http://localhost:4000", "http://localhost:3000", "http://127.0.0.1:4000", "http://127.0.0.1:3000", "http://localhost:9000"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
) # CORS middleware to allow cross-origin requests

# Mount static files
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

app.include_router(api_router, prefix=f"{settings.API_PREFIX}/v1")

if __name__ == "__main__":
    try:
        port = settings.PORT
        host = "0.0.0.0"
        workers = os.cpu_count()  # Use the number of CPU cores as the number of workers

        app_logger.log_info(f"Starting server on {host}:{port}")
        app_logger.log_info(f"Workers configured: {settings.UVICORN_WORKER_COUNT}")
        app_logger.log_info(f"CPU cores available: {workers}")
        app_logger.log_info(f"Environment: {settings.ENVIRONMENT}")
        app_logger.log_info(f"Log level: info")

        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=settings.UVICORN_WORKER_COUNT,
            log_level="info",
            reload=False
        )
    except KeyboardInterrupt:
        app_logger.log_info("Server shutdown requested by user")
    except Exception as e:
        app_logger.log_error("Failed to start the server", exc_info=e)
        raise e
    finally:
        app_logger.log_info("Server shutdown complete")

