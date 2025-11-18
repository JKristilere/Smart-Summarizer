from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Chroma settings (Required)
    CHROMA_API_KEY: str
    CHROMA_TENANT: str
    CHROMA_DATABASE: str

    # LLM Settings (Required)
    GROQ_API_KEY: str
    
    # Ollama Settings (Optional)
    OLLAMA_API_KEY: Optional[str] = ""
    OLLAMA_HOST: Optional[str] = "http://localhost:11434"
    OLLAMA_MODEL: Optional[str] = "llama3"

    # Database Settings
    DATABASE_URI: str  # Main connection string (Required)
    
    # Individual PostgreSQL fields (Optional - for backward compatibility)
    POSTGRES_USER: Optional[str] = "summarizer"
    POSTGRES_PASSWORD: Optional[str] = ""
    POSTGRES_PORT: Optional[str] = "5432"
    POSTGRES_DB: Optional[str] = "summarizer_db"
    POSTGRES_HOST: Optional[str] = "localhost"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Create a global settings instance
settings = Settings()