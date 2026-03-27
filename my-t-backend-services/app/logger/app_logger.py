import os
import logging
import sys
from loguru import logger
from typing import Any
import re

# Ensure the logs directory exists (use /tmp on read-only filesystems like Vercel)
_logs_dir = "/tmp/logs" if not os.access(".", os.W_OK) else "logs"
os.makedirs(_logs_dir, exist_ok=True)

def format_log_message(record):
    """Extract class name from message and format it properly with fixed width"""
    message = record.get("message", "")
    class_name_match = re.search(r'\[([A-Za-z_][A-Za-z0-9_]*)\]', message)

    if class_name_match:
        class_name = class_name_match.group(1)
        clean_message = re.sub(r'\[([A-Za-z_][A-Za-z0-9_]*)\]\s*', '', message)
        # Pad class name to fixed width of 24 characters for proper alignment
        padded_class_name = f"{class_name:<24}"
        record["extra"]["class_name"] = padded_class_name
        record["extra"]["clean_message"] = clean_message
        record["extra"]["class_name_separator"] = " | "
        return True
    else:
        # Use dashes when no class name
        record["extra"]["class_name"] = "-" * 24
        record["extra"]["clean_message"] = message
        record["extra"]["class_name_separator"] = " | "
        return False

LOG_FILE = f"{_logs_dir}/app.log"

# Remove default Loguru handler to avoid duplicates
logger.remove()

# Configure Loguru Logger with custom filename - FULL logging to file
logger.add(
    LOG_FILE,
    rotation="1 day",
    retention="10 days",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{file}</cyan>:<cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    serialize=False,
    enqueue=True,
    level="DEBUG"  # Log everything to file
)

# Add clean console handler - FILTERED for readability
def console_filter(record):
    """Filter and format console logs"""
    # First apply the basic filters
    if not (record["level"].no >= 20 and  # INFO level and above
            not record["name"].startswith("pymongo") and  # Filter out MongoDB logs
            not record["name"] == "logging" and  # Filter out logging module debug messages
            not record["name"].startswith("passlib")):  # Filter out passlib logs
        return False

    # Format the message to extract class name
    format_log_message(record)
    return True

logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{extra[class_name]}</level>{extra[class_name_separator]}<cyan>{name}</cyan> - <level>{extra[clean_message]}</level>",
    level="INFO",
    filter=console_filter
)

# Configure standard Python logging to redirect to Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Replace standard logging handlers with Loguru interceptor
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Ensure uvicorn logs are captured
for name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
    logging.getLogger(name).handlers = [InterceptHandler()]

# Reduce logging verbosity for various modules
for name in [
    "pymongo", "pymongo.command", "pymongo.connection", "pymongo.server", "pymongo.topology",
    "passlib", "passlib.handlers", "passlib.handlers.bcrypt",
    "asyncio", "asyncio.selector_events"
]:
    logging.getLogger(name).setLevel(logging.WARNING)

# Set root logger to INFO to reduce general debug noise
logging.getLogger().setLevel(logging.INFO)


class AppLogger:
    """Logging class using Loguru for structured logging. Provides synchronous and asynchronous logging capabilities."""

    def __init__(self) -> None:
        pass

    def log_info(self, *args: Any, **kwargs: Any) -> None:
        """Logs an info message."""
        level = kwargs.pop("level", "INFO")
        message = " ".join(map(str, args))
        logger.opt(depth=1).log(level, message, **kwargs)

    async def async_log_info(self, *args: Any, **kwargs: Any) -> None:
        """Logs an info message asynchronously."""
        level = kwargs.pop("level", "INFO")
        message = " ".join(map(str, args))
        logger.opt(depth=1).log(level, message, **kwargs)

    def log_error(self, *args: Any, **kwargs: Any) -> None:
        """Logs an error message."""
        message = " ".join(map(str, args))
        logger.opt(depth=1).error(message, **kwargs)

    async def async_log_error(self, *args: Any, **kwargs: Any) -> None:
        """Logs an error message asynchronously."""
        message = " ".join(map(str, args))
        logger.opt(depth=1).error(message, **kwargs)

    def log_debug(self, *args: Any, **kwargs: Any) -> None:
        """Logs a debug message."""
        message = " ".join(map(str, args))
        logger.opt(depth=1).debug(message, **kwargs)

    async def async_log_debug(self, *args: Any, **kwargs: Any) -> None:
        """Logs a debug message asynchronously."""
        message = " ".join(map(str, args))
        logger.opt(depth=1).debug(message, **kwargs)

    def log_warning(self, *args: Any, **kwargs: Any) -> None:
        """Logs a warning message."""
        message = " ".join(map(str, args))
        logger.opt(depth=1).warning(message, **kwargs)

    async def async_log_warning(self, *args: Any, **kwargs: Any) -> None:
        """Logs a warning message asynchronously."""
        message = " ".join(map(str, args))
        logger.opt(depth=1).warning(message, **kwargs)


# Instantiate global logger instance
app_logger = AppLogger()