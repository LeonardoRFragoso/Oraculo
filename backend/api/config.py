"""
Configurações da API
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Aplicação
    APP_NAME: str = "Oráculo API"
    VERSION: str = "3.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Autenticação
    REQUIRE_AUTH: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.7
    
    # OpenRAG
    USE_OPENRAG: bool = os.getenv("USE_OPENRAG", "false").lower() == "true"
    OPENRAG_API_URL: str = os.getenv("OPENRAG_API_URL", "http://localhost:7860")
    OPENSEARCH_URL: str = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    DOCLING_URL: str = os.getenv("DOCLING_URL", "http://localhost:5001")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".xlsx", ".xls", ".csv", ".pdf", ".docx", ".txt", ".json"
    ]
    UPLOAD_DIR: str = "../dados/uploads"
    
    # Cache
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1 hora
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "../logs/api.log"
    
    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"  # Ignorar campos extras do .env


settings = Settings()
