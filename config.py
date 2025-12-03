"""
Configuration management for Enterprise RAG
Uses environment variables with sensible defaults
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS Configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # LLM Configuration
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "llama3")
    
    # RAG Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    RETRIEVAL_K: int = int(os.getenv("RETRIEVAL_K", "5"))
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: list = os.getenv("ALLOWED_EXTENSIONS", "pdf").split(",")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    
    # Database Configuration
    DB_STORAGE_PREFIX: str = os.getenv("DB_STORAGE_PREFIX", "db_storage")
    
    # Audio Configuration
    TTS_LANGUAGE: str = os.getenv("TTS_LANGUAGE", "en")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)

# Create global config instance
config = Config()


