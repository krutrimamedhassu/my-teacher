import os
from enum import Enum
from typing import Any, List, Optional
from app.logger.app_logger import app_logger
from pydantic_settings import BaseSettings


class AppEnvironment(str, Enum):
    """Enum for app environments."""
    LOCAL = "local"
    DEV = "dev"
    QA = "qa"
    PROD = "prod"


class Settings(BaseSettings):
    """
    Application settings.
    
    These settings can be overridden with environment variables.
    """
    # Project information
    PROJECT_NAME: str
    API_PREFIX: str

    # Environment settings
    DEFAULT_MODEL: str
    OPENAI_API_KEY: Optional[str]
    MONGODB_URI: Optional[str]
    MONGODB_TEST_DB: str

    # Document store settings
    DOCUMENT_STORE_INVOKER_URL: str

    # API documentation
    TITLE_OF_THE_PROJECT: str
    DESCRIPTION_OF_THE_PROJECT: str
    VERSION: str
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    

    # Document handling settings
    MAX_DOCUMENT_SIZE_MB: int
    ALLOWED_DOCUMENT_TYPES: List[str]

    # Embedding settings
    EMBEDDING_MODEL: str
    VECTOR_STORE_PATH: str

    # Logging settings
    LOG_LEVEL: str

    # Logfire settings
    LOGFIRE_TOKEN: Optional[str] = None

    # Server settings
    PORT: int

    # LLM settings for generate_text in GenerativeResponder
    MAX_TOKENS_GEN_TEXT: int

    # Streaming settings
    STREAMING_MODEL: Optional[str] = None
    STREAMING_CHUNK_SIZE: int = 20

    # TTS settings
    TTS_MODEL: str = "tts-1"
    TTS_VOICE: str = "alloy"

    @property
    def ENVIRONMENT(self) -> AppEnvironment:
        """Returns the app environment."""
        return AppEnvironment[os.getenv("AI_ENV", default="local").upper()]

    @property
    def UVICORN_WORKER_COUNT(self) -> int:
        """Calculates the number of Uvicorn workers based on the environment."""
        if self.ENVIRONMENT == AppEnvironment.LOCAL:
            return 1
        return 4  # Example value; adjust based on your server configuration.

    class Config:
        env_file = None  # Disable default env_file setting
        extra = 'allow'


def load_settings() -> Settings:
    """
    Load settings and handle missing environment files gracefully.

    Returns:
        Settings: The loaded settings instance.
    """
    app_logger.log_info("Current directory -->", os.getcwd())
    environment = os.getenv("AI_ENV", "local")  # Default to "local" if not set
    env_file = f".env.{environment}"

    app_logger.log_info(f"Using env file: {env_file}")

    if not os.path.exists(env_file):
        app_logger.log_warning(f"Environment file {env_file} not found. Defaults may be used.")
        return Settings()  # Load default settings, will fail for required fields unless explicitly set.

    # Create the Settings instance with the chosen environment file
    return Settings(_env_file=env_file)


# Load Settings instance
settings = load_settings()