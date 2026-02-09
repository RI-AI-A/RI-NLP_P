"""API Configuration"""
from pydantic_settings import BaseSettings
from typing import List


class APIConfig(BaseSettings):
    """API Service Configuration"""
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API Metadata
    api_title: str = "Retail Intelligence NLP Service"
    api_description: str = "Production-grade NLP microservice for retail analytics"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Singleton instance
api_config = APIConfig()
