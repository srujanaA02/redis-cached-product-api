import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application configuration settings loaded from environment variables."""
    
    # API Configuration
    API_PORT: int = int(os.getenv("API_PORT", "8080"))
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./products.db")
    
    # Application Settings
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


# Create a global settings instance
settings = Settings()
