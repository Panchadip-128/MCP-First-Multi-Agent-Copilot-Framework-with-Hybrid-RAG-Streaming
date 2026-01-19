"""
Configuration management using Pydantic Settings.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "LLM Copilot Framework"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://localhost:8000",
        "http://localhost:5173",  # Vite default dev server
    ]
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./copilot.db", validation_alias="DATABASE_URL")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", validation_alias="REDIS_URL")
    
    # Vector DB (Weaviate)
    VECTOR_DB_URL: str = Field(default="http://localhost:8080", validation_alias="VECTOR_DB_URL")

    # Workspace
    WORKSPACE_ROOT: str = Field(default="/mnt/d/proj1", validation_alias="WORKSPACE_ROOT")
    
    # LLM Providers
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    GROQ_API_KEY: str = Field(default="", validation_alias="GROQ_API_KEY")
    
    # Embedding Model (using OpenAI)
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    EMBEDDING_PROVIDER: str = Field(default="openai", validation_alias="EMBEDDING_PROVIDER")
    GROQ_EMBEDDING_MODEL: str = Field(default="", validation_alias="GROQ_EMBEDDING_MODEL")
    
    # RAG Settings
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5
    RAG_SEARCH_MODE: str = Field(default="hybrid", validation_alias="RAG_SEARCH_MODE")
    
    # Agent Settings
    DEFAULT_LLM_PROVIDER: str = "groq"
    DEFAULT_LLM_MODEL: str = "llama-3.1-8b-instant"
    MAX_TOOL_ITERATIONS: int = 10
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", validation_alias="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
